import socket, os, threading

class MockPSECSysUsbInputs():
    dom0_socket = None
    dom0_socket_path = ""    

    def start(self, sockets_path:str):
        self.dom0_socket_path = "{}/sys-usb-input.sock".format(sockets_path)
        
        print("Opening sys-usb@Dom0 I/O socket at {}".format(self.dom0_socket_path))        

        if os.path.exists(self.dom0_socket_path):
            os.remove(self.dom0_socket_path)

        self.dom0_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.dom0_socket.bind(self.dom0_socket_path)
        self.dom0_socket.listen(1)

        threading.Thread(target= self.__monitor_socket).start()

    def __monitor_socket(self):
        while True:
            conn, _ = self.dom0_socket.accept()
            print(f"Connection received on Dom0 sys-usb I/O socket")

            try:
                while True:
                    data = conn.recv(128)
                    
                    if not data:
                        break

                    print("DEBUG - Received {} bytes on sys-usb Dom0 I/O socket".format(len(data)))
                    print("DEBUG - {}".format(data))
            finally:
                conn.close()
                self.dom0_socket.close()
                os.remove(self.dom0_socket_path)
                print("Socket removed")