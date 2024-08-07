from PySide6.QtCore import QObject, Signal, qDebug, qWarning
from PySide6.QtCore import QProcess, QTimer, QDir, Property, Slot, QPoint
from psec import Journal, MessagerieDomu, Message
import threading

class InterfaceSocle(QObject):
    "Cette classe surveille le XenBus pour récupérer des informations"
    "sur les périphériques d'entrée communiquant au travers du XenBus."
    "Voir panoptiscan-vm-sys-usb/monitor-touchscreen.py"

    journal = Journal("Contrôleur")

    # Signaux
    pret = Signal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    @Slot()
    def demarreSurveillance(self):        
        try:
            MessagerieDomu().set_demarrage_callback(self.__on_messagerie_prete)
            MessagerieDomu().set_message_callback(self.__on_message_recu)
        except Exception as e:
            self.journal.error("La connexion à la messagerie a échoué")
            self.journal.error(e)
            return
        
    @Slot()
    def arreteSurveillance(self):
        self.journal.debug("Arrêt de l'interface de messagerie")        

    def onNouvellePosition(self, val):
        # Une position est un tuple codé "X,Y"
        if b"," in val:
            spl = val.split(b",")
            if len(spl) != 2:
                qDebug('La valeur {0} est mal encodée. Format attendu : "X,Y"'.format(val))
            else:
                try:
                    x = int(spl[0])
                    y = int(spl[1])

                    self.xenbusEvent.emit( ( EVENT_POS_SOURIS, QPoint(x,y) ) )
                except ValueError as e:
                    qDebug('La valeur {0} est mal encodée. Format attendu : "X,Y"'.format(val))
        else:
            qDebug('La valeur {0} est mal encodée. Format attendu : "X,Y"'.format(val))

    def __on_messagerie_prete(self):
        self.pret.emit()

    def __on_message_recu(self, message : Message):
        pass