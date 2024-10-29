from psec import Journal, MessagerieDomu, Message, Commande, TypeMessage, Reponse, TypeCommande, ReponseFactory, Parametres, Cles, EtatComposant
from mock_saphir_mockav import MockSaphirAV

class MockSaphirAVController:
    ''' This class mocks a listener located in a DomU dedicated to file analysis.
    
    It listens to commands on the Messaging socket, executes analyses and returns the result.
    '''

    mount_point = "/tmp/mockpsec/mount_point"
    logger = Journal("Mock AV Controller")
    mockav = MockSaphirAV()

    def __init__(self) -> None:
        pass

    def start(self, socket_path:str) -> None:
        self.logger.info("Starting Mock AV Controller")

        MessagerieDomu().set_message_callback(self.__message_callback)
        MessagerieDomu().set_demarrage_callback(self.__demarrage_callback)
        MessagerieDomu().demarre(force_serial_port= socket_path)

    def __demarrage_callback(self) -> None:
        self.logger.info("Le contrôleur Mock AV a démarré")

    def __message_callback(self, msg:Message) -> None:
        self.logger.debug("Message reçu sur le contrôleur Mock AV")

        if msg.type == TypeMessage.COMMANDE:
            commande:Commande = msg

            if commande.commande == TypeCommande.LISTE_COMPOSANTS:
                self.__get_component_state(msg.source)

    #########
    # Fonctions privées
    ###
    def __get_component_state(self, source:str) -> None:
        ''' Retourne l'état courant des composants
            Si la messagerie est prête, le domaine est prêt
        '''

        reponse = ReponseFactory.cree_reponse_etat_composant("mock_av", EtatComposant.OK)
        reponse.destination = source
        MessagerieDomu().envoie_message_xenbus(reponse)