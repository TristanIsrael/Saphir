import unittest
from copy import deepcopy
import time
from threading import Event, Lock
from safecor import Api, MqttFactory, Topics, NotificationFactory, Constants, DiskState, ResponseFactory
from Saphir import AnalysisController, AnalysisState, AnalysisMode
from libsaphir import TOPIC_ANALYSIS, FileStatus

class TestAnalysisController(unittest.TestCase):

    STORAGE_FILES = {"disk": "Archives", "files": [{"type": "file", "path": "/", "name": ".DS_Store", "size": 6148}, {"type": "file", "path": "/", "name": "Test.pdf", "size": 2772992}]}
    ARCHIVE_FILES = [{"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "exefs.nsp", "size": 572907}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103/flags", "name": "boot2.flag", "size": 0}, {"type": "file", "path": "/1.3.0/atmosphere/contents/4200000000003103", "name": "toolbox.json", "size": 113}, {"type": "file", "path": "/1.3.0/switch/.overlays", "name": "parental_control.ovl", "size": 1065016}]
    ANALYSIS_COMPONENTS = [
        {"id": "av1", "domain_name": "Mac", "label": "Mock ESET antivirus", "type": "antivirus", "state": "ready", "version": "1.0.0-mock", "description": "Version mock"},
        {"id": "av2", "domain_name": "Mac", "label": "ClamAV Antivirus controller", "type": "antivirus", "state": "ready", "version": "ClamAV 1.4.2/27164/Wed Jan 24 10:45:32 2024", "description": ""}
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
        Api().subscribe(f"{Topics.DISKS}/+/request")
        self.__analysis_controller = AnalysisController(self.__files_queue, self.ANALYSIS_COMPONENTS, "Archives", AnalysisMode.AnalyseSelection)

    def __on_subscribed(self, mid):
        self.__nb_subscriptions = self.__nb_subscriptions + 1
        if self.__nb_subscriptions == 3:
            self.__ready_event.set()

    def __on_message(self, topic:str, payload:dict):        
        # We ignore our own messages
        if topic == Topics.NEW_FILE:
            return
        elif topic.endswith("/response") and not topic.startswith(TOPIC_ANALYSIS):
            return
        elif topic == Topics.DISK_STATE:
            return

        self.__message_lock.acquire()
        if topic.startswith(Topics.SYSTEM_INFO):
            resp_payload = {
                "system": { "machine": { "cpu": 16 }}
            }
            self.__mqtt_client.publish(f"{Topics.SYSTEM_INFO}/response", resp_payload)
        
        self.__messages_recv.append({ "topic": topic, "payload": payload})
        #print(self.__messages_recv)

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
        self.assertEqual(self.__messages_recv[1]["payload"], {"disk": "Archives", "filepath": "/.DS_Store"})
        self.assertEqual(self.__messages_recv[2]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[2]["payload"], {"disk": "Archives", "filepath": "/Test.pdf"})

        self.__messages_recv.clear()

        # We send the new file notification for the first file
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/.DS_Store", "abcdef0123456789", "abcdef0123456789")
        self.__nb_expected_messages = 1
        self.__message_event.clear()
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        self.assertTrue(self.__message_event.wait())
        
        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"filepath": "/.DS_Store"})

        time.sleep(0.1)

        # The file status should have changed
        file = self.__files_queue.get("/.DS_Store", {})
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAvailableInRepository)

        # Now the analysis request has been sent we send progress information
        payload = {
            "component": "av_test",
            "filepath": "/.DS_Store",
            "status": FileStatus.FileAnalysing.value,
            "progress": 10
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/status", payload)

        # We wait a little...
        time.sleep(0.5)

        # Now we verify that the progress has been updated        
        self.assertEqual(file.get("progress", 0), 0) # The status is ignored now

        # We send a result
        payload = {
            "component": "av1",
            "filepath": "/.DS_Store",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # We wait a little...
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 50)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)
        
        # Then we send the second component result
        payload = {
            "component": "av2",
            "filepath": "/.DS_Store",
            "success": False,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 100)
        self.assertEqual(file.get("status", FileStatus.FileAnalysing), FileStatus.FileInfected)

        # After that we analyse the second file
        payload = {
            "component": "av1",
            "filepath": "/Test.pdf",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        file = self.__files_queue.get("/Test.pdf", {})
        self.assertEqual(file.get("progress", 0), 50)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Final result
        payload = {
            "component": "av2",
            "filepath": "/Test.pdf",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        file = self.__files_queue.get("/Test.pdf", {})
        self.assertEqual(file.get("progress", 0), 100)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileClean)

    def test_scan_archive(self):
        # Verify subscriptions
        self.assertTrue(self.__ready)

        # Wait for the init message
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.assertTrue(self.__message_event.wait(1))
        self.assertEqual(len(self.__messages_recv), 1)

        # Update the queue with an archive
        self.__update_queue([{"type": "file", "path": "/", "name": "Test.iso", "size": 50000000}])

        self.__messages_recv.clear()
        self.__message_event.clear()                
        self.__nb_expected_messages = 2
        self.__analysis_controller.start_analysis()
        self.assertEqual(self.__analysis_controller.get_analysis_state(), AnalysisState.AnalysisRunning)
        # Wait for the Analysis/resume message
        self.assertTrue(self.__message_event.wait(2))

        # Verify the message received        
        self.assertEqual(len(self.__messages_recv), 2)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/resume")
        self.assertEqual(self.__messages_recv[1]["topic"], f"{Topics.MOUNT_FILE}/request")
        self.assertEqual(self.__messages_recv[1]["payload"], {"disk": "Archives", "filepath": "/Test.iso"})
        
        # We send the notification that the file has been mounted
        self.__messages_recv.clear()
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        payload = NotificationFactory.create_notification_disk_state("Test.iso", DiskState.MOUNTED)
        self.__mqtt_client.publish(Topics.DISK_STATE, payload)

        # The controller will send us a files list request
        self.__message_event.wait(1)
        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{Topics.LIST_FILES}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"disk": "Test.iso", "recursive": True, "from_dir": ""})

        # We answer with the list of files
        self.__messages_recv.clear()
        self.__message_event.clear()
        self.__nb_expected_messages = 4
        payload = ResponseFactory.create_response_list_files("Test.iso", self.ARCHIVE_FILES)
        self.__mqtt_client.publish(f"{Topics.LIST_FILES}/response", payload)

        # Now we expect some queries by the controller
        self.__message_event.wait(1)
        self.assertEqual(len(self.__messages_recv), 4)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"disk": "Test.iso", "filepath": "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"})
        self.assertEqual(self.__messages_recv[1]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[1]["payload"], {"disk": "Test.iso", "filepath": "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"})
        self.assertEqual(self.__messages_recv[2]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[2]["payload"], {"disk": "Test.iso", "filepath": "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"})
        self.assertEqual(self.__messages_recv[3]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[3]["payload"], {"disk": "Test.iso", "filepath": "/1.3.0/switch/.overlays/parental_control.ovl"})

        # And we answer that the files are in the repository
        # We expect the controller to send analysis requests for the files
        self.__messages_recv.clear()
        self.__nb_expected_messages = 4
        self.__message_event.clear()
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp", "abcdef0123456789", "abcdef0123456789")
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag", "abcdef0123456789", "abcdef0123456789")
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json", "abcdef0123456789", "abcdef0123456789")
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/1.3.0/switch/.overlays/parental_control.ovl", "abcdef0123456789", "abcdef0123456789")                
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        
        self.assertTrue(self.__message_event.wait(1))
        
        self.assertEqual(len(self.__messages_recv), 4)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"filepath": "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp"})
        self.assertEqual(self.__messages_recv[1]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[1]["payload"], {"filepath": "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag"})
        self.assertEqual(self.__messages_recv[2]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[2]["payload"], {"filepath": "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json"})
        self.assertEqual(self.__messages_recv[3]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[3]["payload"], {"filepath": "/1.3.0/switch/.overlays/parental_control.ovl"})        

        # We send a result
        payload = {
            "component": "av1",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # We wait a little...
        time.sleep(0.5)

        # We verify the values
        file = self.__files_queue.get("/Test.iso", {})
        self.assertEqual(file.get("progress", 0), 12.5)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)
        
        # Then we send the second component result
        payload = {
            "component": "av2",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp",
            "success": False,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 25.0)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # After that we analyse the second file
        payload = {
            "component": "av1",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 37.5)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Next component
        payload = {
            "component": "av2",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 50.0)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Next file
        payload = {
            "component": "av1",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 62.5)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Next component
        payload = {
            "component": "av2",
            "filepath": "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 75.0)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Last file
        payload = {
            "component": "av1",
            "filepath": "/1.3.0/switch/.overlays/parental_control.ovl",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 87.5)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileAnalysing)

        # Next component
        payload = {
            "component": "av2",
            "filepath": "/1.3.0/switch/.overlays/parental_control.ovl",
            "success": True,
            "details": "Some details"
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # Wait a little
        time.sleep(0.1)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 100.0)
        self.assertEqual(file.get("status", FileStatus.FileStatusUndefined), FileStatus.FileInfected)
        

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
        self.__files_queue.clear()

        for f in files_list:
            filepath = f"{"" if f.get("path") == "/" else f.get("path")}/{f.get("name")}"
            f["filepath"] = filepath
            f["inqueue"] = True
            self.__files_queue[filepath] = f
