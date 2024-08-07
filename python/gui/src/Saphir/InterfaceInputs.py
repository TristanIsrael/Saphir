from PySide6.QtCore import QObject, Signal, qDebug, qWarning
from PySide6.QtCore import QProcess, QTimer, QDir, Property, Slot, QPoint, QCoreApplication, Qt, QEvent, QSize
from PySide6.QtGui import QMouseEvent, QCursor
from PySide6.QtWidgets import QWidget
from MousePointer import MousePointer
from psec import Journal, Parametres, Cles, Mouse, MouseButton
import threading, serial, pickle

class InterfaceInputs(QObject):
    """! Cette classe traite les informations sur les entrées (clavier, souris et tactile) en provenance du socle.

    """

    journal = Journal("InterfaceInputs")
    fenetre_app:QWidget = None
    dernier_bouton = Qt.NoButton
    #curseurController = CurseurController()
    chemin_socket_inputs = None   
    socket_inputs = None 
    mouse = Mouse()
    #current_buttons = 0

    # Signaux
    pret = Signal()
    nouvellePosition = Signal(QPoint)

    def __init__(self, fenetre_app:QWidget, parent:QObject=None):
        QObject.__init__(self, parent)
        self.fenetre_app = fenetre_app

    #def setCurseurController(self, ctrl:CurseurController):
    #    self.curseurController = ctrl

    @Slot()
    def demarre_surveillance(self):        
        try:
            self.chemin_socket_inputs = Parametres().parametre(Cles.CHEMIN_SOCKET_INPUT_DOMU)
            th = threading.Thread(target=self.__connecte_interface_xenbus)
            th.start()
        except:
            self.journal.error("Impossible d'ouvrir le port Xenbus Inputs")

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
        self.journal.debug("Ouvre le flux avec le port série Inputs %s" % self.chemin_socket_inputs)

        try:
            self.socket_inputs = serial.Serial(port= self.chemin_socket_inputs)
            self.journal.info("La surveillance des entrées est démarrée")     
            self.pret.emit()       
        
            while True:
                data = self.socket_inputs.read_until(b'\n') 

                #if data:
                #print("Données reçues depuis le Xenbus : {0}".format(data))
                self.__traite_donnees_input(data[:-1])
        except serial.SerialException as e:
            self.socket_inputs = None
            self.journal.error("Impossible de se connecter au port série %s" % self.chemin_socket_inputs)
            self.journal.error(e)    

    def __traite_donnees_input(self, data:bytes):
        # On recoit une version sérialisée d'un objet
        # Pour l'instant on ne traite que la classe Mouse
        mouse = Mouse.fromData(data)
        if mouse != None:
            self.__traite_donnees_souris(mouse)

    def __traite_donnees_souris(self, mouse:Mouse):
        newX = self.mouse.x + mouse.x
        newY = self.mouse.y + mouse.y
        self.mouse.x = max(0, min(self.fenetre_app.width(), newX))
        self.mouse.y = max(0, min(self.fenetre_app.height(), newY))
        screenPos = QPoint(self.mouse.x, self.mouse.y)
        
        # On émet le signal de la nouvelle position
        self.nouvellePosition.emit(screenPos)

        # Ensuite on regarde s'il y a eu un changement sur les boutons
        if not self.mouse.buttons_equal(mouse):
            self.__verifie_bouton_souris(mouse, MouseButton.LEFT, screenPos)
            self.__verifie_bouton_souris(mouse, MouseButton.MIDDLE, screenPos)
            self.__verifie_bouton_souris(mouse, MouseButton.RIGHT, screenPos)
            self.mouse.buttons = mouse.buttons

    def __verifie_bouton_souris(self, mouse:Mouse, button: int, screenPos: int):
        qbutton = Qt.LeftButton if button == MouseButton.LEFT else Qt.MiddleButton if button == MouseButton.MIDDLE else Qt.RightButton

        if not mouse.button_equals(self.mouse, button):
            if self.mouse.button_pressed(MouseButton.LEFT):
                self.__genereMouseEvent(QEvent.MouseButtonPress, screenPos, screenPos, qbutton, qbutton, self.fenetre_app)
            else:
                self.__genereMouseEvent(QEvent.MouseButtonRelease, screenPos, screenPos, qbutton, qbutton, self.fenetre_app)

    def __genereMouseEvent(self, eventType: QEvent.Type, localPos: QPoint, screenPos: QPoint, button: Qt.MouseButton, buttons: Qt.MouseButtons, cible: QObject):
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
        qDebug("Génération d'un événement {} aux coordonnées locales ({},{}) / écran ({},{})".format(eventType, localPos.x(), localPos.y(), screenPos.x(), screenPos.y()))

        # Création des événements press et release pour la souris
        event = QMouseEvent(eventType, localPos, screenPos, button, buttons, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.postEvent(cible, event)