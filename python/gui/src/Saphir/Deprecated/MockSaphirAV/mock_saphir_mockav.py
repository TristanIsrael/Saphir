from psec import MessagerieDomu, Journal, Message, TypeMessage, Commande, Parametres, Cles
import threading, time, os, sys, subprocess
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir)
from AbstractAntivirusController import AbstractAntivirusController

class MockSaphirAV(AbstractAntivirusController):
    ''' This class manages the antivirus analysis.

    The controller listens on the messaging socket and waits for commands. When a command is sent, it
    starts and monitors the analysis of one particular file of the repository. When done it sends an 
    Answer to the requester and gives details on the analysis result.
    '''    

    def __init__(self):
        super().__init__("Mock AV")

    def _execute_command_analyse_file(self, command:Commande):
        self.logger().info("[Mock AV] Command : analyse file")

        file_path = command.arguments.get("filepath")
        fingerprint = command.arguments.get("fingerprint")

        repo_path = "{}/{}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU), file_path)

        self.logger().info("Starting analysis for {}".format(file_path))
        self.logger().debug("File location is {}".format(repo_path))

        res = subprocess.run(args= ["clamdscan", repo_path], capture_output= True)
    
        self.send_result(
            file_path=file_path,
            infected= res.returncode not in (0, 2),
            error= res.returncode == 2,
            message= res.stderr.decode()
        )

        self.command_finished()

if __name__ == "__main__":    
    m = MockAntivirusController("Mock AV controller")
    #m.start()

    # Surcharge des paramètres d'environnement pour le test
    Parametres().set_parametre(Cles.STORAGE_PATH_DOMU, "/tmp/mockpsec/mount_point")

    cmd = Commande("analyze_file", { "filepath": "/Saphir/Panoptiscan.qmlproject" })
    m._execute_command_analyse_file(cmd)
    