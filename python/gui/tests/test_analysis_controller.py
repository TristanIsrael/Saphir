import unittest
from copy import deepcopy
import time
from threading import Event, Lock
from safecor import Api, MqttFactory, Topics, ResponseFactory
from Saphir import AnalysisController, AnalysisState, AnalysisMode
from libsaphir import TOPIC_ANALYSIS, FileStatus

class TestAnalysisController(unittest.TestCase):

    STORAGE_FILES = {"disk": "Archives", "files": [{"type": "file", "path": "/", "name": ".DS_Store", "size": 6148}, {"type": "file", "path": "/", "name": "Test.pdf", "size": 2772992}]}
    ARCHIVE_FILES = {"disk": "Test.iso", "files": [{"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "exefs.nsp", "size": 572907}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103/flags", "name": "boot2.flag", "size": 0}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "toolbox.json", "size": 113}, {"type": "file", "path": "/1.3.0/switch/.overlays", "name": "parental_control.ovl", "size": 1065016}]}
    ANALYSIS_COMPONENTS = [
        {"id": "Mock ESET", "domain_name": "Mac", "label": "Mock ESET antivirus", "type": "antivirus", "state": "ready", "version": "1.0.0-mock", "description": "Version mock"},
        {"id": "ClamAV", "domain_name": "Mac", "label": "ClamAV Antivirus controller", "type": "antivirus", "state": "ready", "version": "ClamAV 1.4.2/27164/Wed Jan 24 10:45:32 2024", "description": ""}
    ]    

    def setUp(self):
        self.__ready = False
        self.__ready_event = Event()
        self.__message_event = Event()
        self.__messages_recv = []
        self.__files_queue = {}    
        self.__nb_subscriptions = 0
        self.__nb_expected_messages = 0
        self.__message_lock = Lock()

        # Start the API
        self.__mqtt_client = MqttFactory.create_mqtt_network_dev(__class__.__name__)
        Api().add_message_callback(self.__on_message)
        Api().add_ready_callback(self.__on_api_ready)
        Api().add_subscription_callback(self.__on_subscribed)
        Api().start(self.__mqtt_client, "local")
        self.__nb_expected_messages = 1
        self.__ready = self.__ready_event.wait(0.5)

    def tearDown(self):
        self.__analysis_controller.stop_analysis()
        Api().stop()

    def __on_api_ready(self):
        Api().subscribe(f"{Topics.SYSTEM_INFO}/request")
        Api().subscribe(f"{TOPIC_ANALYSIS}/#")
        Api().subscribe(f"{Topics.DISKS}/#")
        self.__analysis_controller = AnalysisController(self.__files_queue, self.ANALYSIS_COMPONENTS, "Archives", AnalysisMode.AnalyseSelection)

    def __on_subscribed(self, mid):
        self.__nb_subscriptions = self.__nb_subscriptions + 1
        if self.__nb_subscriptions == 3:
            self.__ready_event.set()

    def __on_message(self, topic:str, payload:dict):        
        if topic.endswith("/response"):
            return

        self.__message_lock.acquire()
        if topic.startswith(Topics.SYSTEM_INFO):
            resp_payload = {
                "system": { "machine": { "cpu": 16 }}
            }
            self.__mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", resp_payload)
        
        self.__messages_recv.append({ "topic": topic, "payload": payload})
        print(self.__messages_recv)

        if len(self.__messages_recv) == self.__nb_expected_messages:
            self.__message_event.set()       

        self.__message_lock.release()
     

    def test_init(self):
        self.__files_queue = self.STORAGE_FILES        

        # Verify subscriptions
        self.assertTrue(self.__ready)
        #self.assertEqual(self.__nb_subscriptions, 3)

        self.assertEqual(self.__analysis_controller.get_analysis_state(), AnalysisState.AnalysisStopped)
        # Wait for a message to arrive
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.__message_event.wait(0.5)        

        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{Topics.SYSTEM_INFO}/request")

        # Wait a little that the controller receives the system information
        time.sleep(0.2)
        
        self.assertEqual(self.__analysis_controller.get_repository_capacity(), 8)
        self.__messages_recv.clear()

        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_size(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_size(), 0)

    def test_scan_files(self):
        # Verify subscriptions
        self.assertTrue(self.__ready)
        #self.assertEqual(self.__nb_subscriptions, 3)

        # Wait for the init message
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.assertTrue(self.__message_event.wait(0.5))
        self.assertEqual(len(self.__messages_recv), 1)
                
        self.__update_queue(self.STORAGE_FILES.get("files", []))

        self.__messages_recv.clear()
        self.__message_event.clear()                
        self.__nb_expected_messages = 3
        self.__analysis_controller.start_analysis()
        self.assertEqual(self.__analysis_controller.get_analysis_state(), AnalysisState.AnalysisRunning)
        # Wait for the Analysis/resume message
        self.assertTrue(self.__message_event.wait(3))

        # Verify the message received        
        self.assertEqual(len(self.__messages_recv), 3)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/resume")
        self.assertEqual(self.__messages_recv[1]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[2]["topic"], f"{Topics.READ_FILE}/request")

    def test_repository_free_slots(self):
        # Verify subscriptions
        self.assertTrue(self.__ready)
        #self.assertEqual(self.__nb_subscriptions, 3)

        # Wait for the init message
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.assertTrue(self.__message_event.wait(0.5))
        self.assertEqual(len(self.__messages_recv), 1)        
        self.__messages_recv.clear()

        # Wait a little more
        time.sleep(0.5)

        slots = self.__analysis_controller._AnalysisController__get_repository_free_slots()
        self.assertEqual(slots, 8)

    def test_next_group_of_files(self):
        # Verify subscriptions
        self.assertTrue(self.__ready)
        #self.assertEqual(self.__nb_subscriptions, 3)

        # Wait for the init message
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.assertTrue(self.__message_event.wait(0.5))
        self.assertEqual(len(self.__messages_recv), 1)
        self.__messages_recv.clear()
        
        queue = deepcopy(self.STORAGE_FILES.get("files", []))
        self.__update_queue(queue)

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(1)
        self.assertEqual(len(files), 1)

        file = files[0]
        self.assertEqual(file["name"], ".DS_Store")

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(2)
        self.assertEqual(len(files), 2)

        file = files[0]
        self.assertEqual(file["name"], ".DS_Store")
        file = files[1]
        self.assertEqual(file["name"], "Test.pdf")

        f = queue[0]
        f["status"] = FileStatus.FileAnalysing
        f = queue[1]
        f["status"] = FileStatus.FileAnalysing
        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(2)
        self.assertEqual(len(files), 0)
        
    def test_reset(self):
        self.__analysis_controller.reset()
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_size(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_size(), 0)

    def __update_queue(self, files_list:list[dict]):
        for f in files_list:
            filepath = f"{"" if f.get("path") == "/" else f.get("path")}/{f.get("name")}"
            f["filepath"] = filepath
            f["inqueue"] = True
            self.__files_queue[filepath] = f
