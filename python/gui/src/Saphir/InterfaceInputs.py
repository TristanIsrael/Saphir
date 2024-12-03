from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtCore import  Slot, QPoint, QCoreApplication, Qt, QEvent, QPointF
from PySide6.QtGui import QMouseEvent, QWheelEvent, QHoverEvent, QEnterEvent, QGuiApplication
from PySide6.QtWidgets import QWidget
from MousePointer import MousePointer
from psec import Parametres, Cles, Mouse, MouseButton, MouseWheel, MouseMove, Api
import serial, subprocess #, threading

class InterfaceInputs(QObject):
    """! Cette classe traite les informations sur les entrées (clavier, souris et tactile) en provenance du socle.

    """
    
    fenetre_app:QWidget = None
    dernier_bouton = Qt.MouseButton.NoButton
    chemin_socket_inputs = None   
    socket_inputs = None 
    mouse = Mouse()

    # Signaux
    pret = Signal()
    nouvellePosition = Signal(QPoint)
    clicked = Signal(QPoint)
    wheel = Signal(MouseWheel)


    def __init__(self, fenetre_app:QWidget, parent:QObject=None):
        QObject.__init__(self, parent)
        self.fenetre_app = fenetre_app
        
    @Slot()
    def demarre_surveillance(self):        
        try:
            Api().info("Démarrage de la surveillance des inputs", "InterfaceInputs")
            self.chemin_socket_inputs = Parametres().parametre(Cles.CHEMIN_SOCKET_INPUT_DOMU)
            self.__connecte_interface_xenbus()
        except Exception as e:
            Api().error("Impossible d'ouvrir le port Xenbus Inputs", "InterfaceInputs")
            Api().error(e, "InterfaceInputs")

    def mock(self):       
        print("MOCK") 
        for x in range(100):
            for y in range(100):
                self.nouvellePosition.emit(QPoint(x, y))        

    ###
    # Fonctions privées
    #
    def __connecte_interface_xenbus(self):
        #Ouvre le flux avec la socket
        Api().debug("Ouvre le flux avec le port série Inputs %s" % self.chemin_socket_inputs, "InterfaceInputs")

        try:
            self.socket_inputs:serial.Serial = serial.Serial(port= self.chemin_socket_inputs)
            Api().info("La surveillance des entrées est démarrée", "InterfaceInputs")     
            self.pret.emit()       
        except serial.SerialException as e:
            Api().error("Impossible de se connecter au port série %s" % self.chemin_socket_inputs, "InterfaceInputs")
            Api().error(e, "InterfaceInputs")  
            return
        
        try:
            while True:
                data = self.socket_inputs.read_until(b'\n') 

                #print("Données reçues depuis le Xenbus : {0}".format(data))
                self.__traite_donnees_input(data[:-1])

        except serial.SerialException as e:
            Api().error("Erreur de lecture sur le port inputs %s" % self.chemin_socket_inputs, "InterfaceInputs")
            Api().error(e, "InterfaceInputs")    

    def __traite_donnees_input(self, data:bytes):
        # On recoit une version sérialisée d'un objet
        # Pour l'instant on ne traite que la classe Mouse
        mouse = Mouse.fromData(data)
        if mouse != None:
            self.__traite_donnees_souris(mouse)

    def __traite_donnees_souris(self, mouse:Mouse):
        # Si c'est du tactile il faut recalculer la position en fonction de la résolution de la dalle tactile
        # Les coordonnées sont transmises en pourcentage des dimensions de la dalle
        newX:float=0.0
        newY:float=0.0

        if mouse.move == MouseMove.RELATIVE:
            newX = self.mouse.x + mouse.x
            newY = self.mouse.y + mouse.y
        elif mouse.move == MouseMove.ABSOLUTE:            
            newCoord = self.__convert_tactile_to_window(mouse)            
            newX = newCoord.x()
            newY = newCoord.y()     
        else:
            Api().error("Erreur de décodage", "InterfaceInputs")
            return
            #print(mouse.x, self.fenetre_app.width(), newX, newY)        

        # On limite aux dimensions de l'écran
        self.mouse.x = max(0, min(self.fenetre_app.width(), newX))
        self.mouse.y = max(0, min(self.fenetre_app.height(), newY))
        screenPos = QPoint(self.mouse.x, self.mouse.y)        
        
        # On traite d'abord le clic de souris
        diff = self.mouse.buttons ^ mouse.buttons
        if self.mouse.buttons != mouse.buttons:
            if diff & MouseButton.LEFT == MouseButton.LEFT:
                self.__genere_evt_bouton_souris(mouse, MouseButton.LEFT, screenPos)
            if diff & MouseButton.MIDDLE == MouseButton.MIDDLE:
                self.__genere_evt_bouton_souris(mouse, MouseButton.MIDDLE, screenPos)
            if diff & MouseButton.RIGHT == MouseButton.RIGHT:
                self.__genere_evt_bouton_souris(mouse, MouseButton.RIGHT, screenPos)
            self.mouse.buttons = mouse.buttons            

            # On émet le signal du clic
            self.clicked.emit(screenPos)

            # Si c'est une souris on s'arrête là
            if mouse.move == MouseMove.RELATIVE:
                return

        # Enfin on gère l'action sur la molette        
        if not self.mouse.wheel_equals(mouse):
            angleDelta = QPoint(0, 120 if mouse.wheel == MouseWheel.UP else -120)
            pixelDelta = QPoint(0, 2 if mouse.wheel == MouseWheel.UP else -2)
            localPos = screenPos # On est en plein écran
            
            #event = QWheelEvent(localPos, screenPos, pixelDelta, angleDelta, Qt.NoButton, Qt.KeyboardModifier.NoModifier, Qt.NoScrollPhase, False)             
            event = QWheelEvent(localPos, screenPos, QPoint(), angleDelta, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.ScrollUpdate, False)
            QCoreApplication.postEvent(self.fenetre_app, event)
            
            self.wheel.emit(mouse.wheel)
            #Api().debug("wheel {}".format(mouse.wheel))            

            self.mouse.wheel = MouseWheel.NO_MOVE
            return

        # On émet le signal de la nouvelle position
        event = QMouseEvent(QEvent.Type.MouseMove, screenPos, screenPos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.postEvent(self.fenetre_app, event)
        self.nouvellePosition.emit(screenPos)

    def __genere_evt_bouton_souris(self, mouse:Mouse, button: int, screenPos: int):
        qbutton = Qt.MouseButton.LeftButton if button == MouseButton.LEFT else Qt.MouseButton.MiddleButton if button == MouseButton.MIDDLE else Qt.MouseButton.RightButton

        # Le tracking des boutons fonctionne de la façon suivante :
        # - si l'état des boutons est différent par rapport à la dernière valeur connue
        #   - alors si c'est le bouton gauche et qu'il est actif : on envoie le signal MouseButtonPress pour le bouton gauche
        #   - etc

        if not mouse.button_equals(self.mouse, button):
            if mouse.button_pressed(button): # Si le bouton est actuellement appuyé
                event = QMouseEvent(QEvent.Type.MouseButtonPress, screenPos, screenPos, qbutton, qbutton, Qt.KeyboardModifier.NoModifier)
                QCoreApplication.postEvent(self.fenetre_app, event)
            else: # Sinon le bouton n'est plus appuyé
                # L'événement MouseButtonRelease doit être différé pour être pris en compte
                #event = QMouseEvent(QEvent.MouseButtonRelease, screenPos, screenPos, qbutton, Qt.NoButton, Qt.KeyboardModifier.NoModifier)
                event = QMouseEvent(QEvent.Type.MouseButtonRelease, screenPos, screenPos, qbutton, qbutton, Qt.KeyboardModifier.NoModifier)
                QCoreApplication.postEvent(self.fenetre_app, event)                

    def __genereMouseEvent(self, eventType: QEvent.Type, localPos: QPoint, screenPos: QPoint, button: Qt.MouseButton, buttons: Qt.MouseButtons):
        """Génère un événement de souris et l'insère dans l'event-loop de Qt

        :param eventType: Le type d'événement à générer
        :type eventType: QEvent.Type
        :param localPos: La position (x,y) de l'événement dans le référentiel du composant cliqué
        :type localPos: QPoint
        :param screenPos: La position (x,y) de l'événement dans le référentiel de l'écran physique
        :type screenPos: QPoint
        :param button: Le bouton de la souris concerné par l'action
        :type button: Qt.MouseButton
        :param buttons: Les boutons de la souris concernés par l'action
        :type buttons: Qt.MouseButtons
        :param cible: L'objet graphique qui va recevoir l'événement (une fenêtre d'application)
        :type cible: QObject
        """
        Api().debug("Génération d'un événement {} aux coordonnées locales ({},{}) / écran ({},{})".format(eventType, localPos.x(), localPos.y(), screenPos.x(), screenPos.y()))

        # Création des événements press et release pour la souris
        event = QMouseEvent(eventType, localPos, screenPos, button, buttons, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.postEvent(self.fenetre_app, event)

    def __mouse_buttons_to_qbuttons(self, mouse:Mouse) -> Qt.MouseButtons:        
        buttons = Qt.MouseButton.NoButton

        if mouse.button_pressed(MouseButton.LEFT):
            buttons &= Qt.MouseButton.LeftButton
        if mouse.button_pressed(MouseButton.MIDDLE):
            buttons &= Qt.MouseButton.MiddleButton
        if mouse.button_pressed(MouseButton.RIGHT):
            buttons &= Qt.MouseButton.RightButton

        return buttons    
    
    def __get_screen_rotation(self) -> int:
        try:
            result = subprocess.run(["/usr/bin/xenstore-read", "domid"], capture_output=True, text=True)
            domid = result.stdout.strip()
            result = subprocess.run(["/usr/bin/xenstore-read", "/local/domain/{}/screen_rotation".format(domid)], capture_output=True, text=True)
            orientation = int(result.stdout)

            return orientation
        except:
            return 0
    
    def __convert_tactile_to_window(self, mouse):        
        #print(mouse.x, mouse.y)
        rotation = self.__get_screen_rotation()

        if rotation == 90:
            posX = mouse.x * self.fenetre_app.height()/100
            posY = mouse.y * self.fenetre_app.width()/100
            x_window = posY
            y_window = self.fenetre_app.height() - posX
        else:
            posX = mouse.x * self.fenetre_app.width()/100
            posY = mouse.y * self.fenetre_app.height()/100
            x_window = posX
            y_window = self.fenetre_app.height() - posY

        #print(posX, posY)
        #print(x_window, y_window)
        
        return QPointF(x_window, y_window)