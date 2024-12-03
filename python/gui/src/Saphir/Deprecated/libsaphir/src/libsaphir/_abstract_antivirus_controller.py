from psec import MessagerieDomu, Journal, Message, TypeMessage, Commande
import threading, time
from abc import ABC, abstractmethod

class AbstractAntivirusController(ABC):
    ''' This class manages the antivirus analysis.

    The controller listens on the messaging socket and waits for commands. When a command is sent, it
    starts and monitors the analysis of one particular file of the repository. When done it sends an 
    Answer to the requester and gives details on the analysis result.
    '''

    __name = "NoName"
    __logger = Journal("AbstractAntivirusController")
    __commands_queue = list()
    __commands_thread = None
    __work_in_progress = False

    def __init__(self, name:str):
        self.__name = name
        self.__logger = Journal(name)

    def start(self):
        self.__logger.info("Starting antivirus controller {}".format(self.__name))
    
        MessagerieDomu().set_demarrage_callback(self.__on_messaging_started)
        MessagerieDomu().set_message_callback(self.__on_message_received)
        MessagerieDomu().demarre()

        # Start the commands thread
        self.__commands_thread = threading.Thread(target= self.__commands_loop)        

    def command_finished(self):
        self.__work_in_progress = False

    def logger(self):
        return self.__logger
    
    def send_result(self, file_path:str, infected:bool, error:bool, message:str):        
        self.__logger.info("Analysis result on file {} is: infected={}, error={}, message={}".format(file_path, infected, error, message))

    def __on_messaging_started(self):
        self.__logger.info("Mock antivirus controller started")
        self.__logger.info("Waiting for messages...")

    def __on_message_received(self, message:Message):
        self.__logger.debug("Message received")
        self.__logger.debug(message.to_json())

        if message.destination == "saphir-av-{}".format(self.__name):
            if message.type != TypeMessage.COMMANDE:
                self.__logger.warn("This is not a command. Ignoring.")
                return 
            
            # We can receive commands while we are executing one so we use
            # a command queue
            self.__commands_queue.append(message)
            if not self.__commands_thread.is_alive():
                self.__commands_thread.start()
            
    def __commands_loop(self, command:Commande):
        ''' If there is a task running or no command in queue we wait a little
            The command executed can be synchronous or asynchronous
            In both modes, the subsystem called by the function __execute_command_analyse_file()
            is responsible of setting the __work_in_progress flag to False in
            order to execute the rest of the commands in the queue.
            This can be done by calling the function command_finished()

            If the function __execute_command_analyse_file() crashes, the flag is
            automatically set to False so the next command will be ran. The developer
            should catch the exceptions inside the function if needed.
            '''
        while True:            
            if not self.__work_in_progress and len(self.__commands_queue) > 0:                
                cmd:Commande = self.__commands_queue[0]
                if cmd.payload.get("command") == "analyze_file":
                    self.__work_in_progress = True
                    try:
                        self._execute_command_analyse_file(cmd)
                    except:
                        self.__logger.error("The command has ended unexpectedly.")
                        self.__work_in_progress = False

            time.sleep(0.5)    

    @abstractmethod    
    def _execute_command_analyse_file(self, command:Commande):
        ''' This function has to be executed synchronously
        '''
        pass

    