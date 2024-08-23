import socket, os, threading
from os.path import expanduser
from psec import MessageHelper, Message, Parametres, Cles

class MockPSECSysUsbMessaging():
    dom0_socket = None
    dom0_socket_path = ""    

    #def __init__(self):
    #    home_dir = expanduser("~")
    #    Parametres().set_parametre(Cles.CHEMIN_MONTAGE_USB, home_dir)

    def start(self, sockets_path:str):
        self.dom0_socket_path = "{}/sys-usb-msg.sock".format(sockets_path)
        
        print("Opening sys-usb@Dom0 messaging socket at {}".format(self.dom0_socket_path))        

        if os.path.exists(self.dom0_socket_path):
            os.remove(self.dom0_socket_path)

        self.dom0_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.dom0_socket.bind(self.dom0_socket_path)
        self.dom0_socket.listen(1)

        threading.Thread(target= self.__monitor_socket).start()

    def __monitor_socket(self):
        while True:
            conn, _ = self.dom0_socket.accept()
            print(f"Connection received on Dom0 sys-usb messaging socket")

            try:
                while True:
                    data = conn.recv(128)
                    
                    if not data:
                        break

                    print("DEBUG - Received {} bytes on Dom0 sys-usb messaging socket".format(len(data)))
                    print("DEBUG - {}".format(data))

                    
            finally:
                conn.close()
                self.dom0_socket.close()
                os.remove(self.dom0_socket_path)
                print("Socket removed")
