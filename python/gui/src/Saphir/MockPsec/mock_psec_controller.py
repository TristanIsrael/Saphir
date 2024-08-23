import os, glob
from os.path import expanduser
from distutils.dir_util import copy_tree
from psec import MockXenbus, ControleurDom0, Parametres, Cles, Constantes, Journal, ControleurVmSysUsb
from mock_psec_sys_gui_inputs import MockPSECSysGuiInputs
from mock_psec_sys_gui_messaging import MockPSECSysGuiMessaging
from mock_psec_sys_usb_inputs import MockPSECSysUsbInputs
from mock_psec_sys_usb_messaging import MockPSECSysUsbMessaging

class MockPSECController():
    xenbus_sys_usb_inputs = MockXenbus()
    xenbus_sys_usb_messaging = MockXenbus()
    xenbus_sys_gui_inputs = MockXenbus()
    xenbus_sys_gui_messaging = MockXenbus()

    xenbus_sockets_path = "/var/tmp"
    sys_usb_controller = None
    mount_point = "/tmp/mockpsec/mount_point"
    
    """
    sys_gui_inputs = MockPSECSysGuiInputs()
    sys_gui_messaging = MockPSECSysGuiMessaging()
    sys_gui_messaging_serial_path = ""
    sys_usb_inputs = MockPSECSysUsbInputs()
    sys_usb_messaging = MockPSECSysUsbMessaging()
    """

    logger = Journal("Mock PSEC Controller")

    def start(self):
        """
            We create the surrounding environment for the application as-if it
            were running on a PSEC system.

            Saphir is supposed to run inside a Domain named "sys-gui", the sockets
            and files are named accordingly.

            Things we need to do:
            - Create a Mock Xenbus for sys-usb I/O
            - Create a Mock Xenbus for sys-gui I/O
            - Create a Mock Xenbus for sys-usb messaging
            - Create a Mock Xenbus for sys-gui messaging
            
            - Create a PSEC Dom0 controller
            - Create a sys-usb controller
        """
        self.logger.debug("Starting mock PSEC Controller")
        
        self.__prepare_environment()

        # Set context variables
        Parametres().set_parametre(Cles.CHEMIN_MONTAGE_USB, self.mount_point)

        # Clean environment
        for f in glob.glob("{}/*.sock".format("/var/tmp")):
            os.remove(f)

        # Create mocked Xenbuses
        self.xenbus_sys_gui_inputs.start("sys-gui", "{}/sys-gui-input.sock".format(self.xenbus_sockets_path))
        self.xenbus_sys_gui_messaging.start("sys-gui", "{}/sys-gui-msg.sock".format(self.xenbus_sockets_path))
        self.xenbus_sys_usb_inputs.start("sys-usb", "{}/sys-usb-input.sock".format(self.xenbus_sockets_path))
        self.xenbus_sys_usb_messaging.start("sys-usb", "{}/sys-usb-msg.sock".format(self.xenbus_sockets_path))

        self.__start_sys_usb_controller()
        self.__start_dom0_controller()

    def __start_sys_usb_controller(self):
        self.logger.debug("Starting sys-usb controller...")

        self.sys_usb_controller = ControleurVmSysUsb()
        self.sys_usb_controller.demarre(serial_port= self.xenbus_sys_usb_messaging.domu_serial_port_path())

    def __start_dom0_controller(self):
        self.logger.debug("Starting Dom0 controller...")
             
        Parametres().set_parametre(Cles.CHEMIN_SOCKETS_MESSAGERIE, self.xenbus_sockets_path)
        Parametres().set_parametre(Cles.CHEMIN_SOCKETS_DOM0, self.xenbus_sockets_path)        
        Parametres().set_parametre(Cles.CHEMIN_SOCKET_INPUT_DOM0, "{}/sys-usb-input.sock".format(self.xenbus_sockets_path))
        Parametres().set_parametre(Cles.CHEMIN_SOCKET_MSG, self.xenbus_sys_gui_messaging.domu_serial_port_path())
        self.logger.debug(self.xenbus_sys_gui_messaging.domu_serial_port_path())
        self.logger.debug(Parametres().parametre(Cles.CHEMIN_SOCKET_MSG))
        
        self.logger.debug("... instanciating controller")
        ControleurDom0().demarre()        
        self.logger.debug("... PSEC Mock controller initialized")
        self.logger.debug(Parametres().parametre(Cles.CHEMIN_SOCKET_MSG))
        
    def __prepare_environment(self):
        self.logger.debug("Prepare environment")

        self.logger.debug("Create Mocked mount point at {}".format(self.mount_point))
        os.makedirs(self.mount_point, exist_ok= True)

        self.logger.debug("Copy some files into it")
        curdir = os.path.dirname(__file__)
        srcdir = os.path.realpath(curdir +"/../../")
        copy_tree(srcdir, self.mount_point)