import unittest
from copy import deepcopy
import time
from PySide6.QtTest import QSignalSpy
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
    STORAGE_MIXED_FILES = {"disk": "Mixed", "files": [{"type":"file", "path": "/", "name": "File.txt", "size": 1234}, {"type": "file", "path": "/", "name": "Test.iso", "size": 50000000}, {"type":"file", "path": "/", "name": "File2.txt", "size": 1234}, {"type": "file", "path": "/", "name": "Test2.iso", "size": 50000000}  ]}

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
        elif topic.endswith("/response"):
            return
        elif topic == Topics.DISK_STATE:
            return
        elif topic == f"{Topics.DELETE_FILE}/request":
            return
        elif topic == Topics.DELETED_FILE:
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

        self.__analysis_controller._AnalysisController__repository_size = 0

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
        self.assertIn(file.get("status", FileStatus.FileStatusUndefined), [FileStatus.FileAvailableInRepository, FileStatus.FileAnalysing])

        # Now that the analysis request has been sent we send progress information
        payload = {
            "component": "av_test",
            "filepath": "/.DS_Store",
            "status": FileStatus.FileAnalysing.value,
            "progress": 10
        }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/status", payload)

        # We wait a little...
        time.sleep(0.5)

        self.assertEqual(self.__analysis_controller.get_repository_size(), 1)

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
        self.assertEqual(self.__analysis_controller.get_repository_size(), 1)
        
        # Then we send the second component result
        payload = {
            "component": "av2",
            "filepath": "/.DS_Store",
            "success": False,
            "details": "Some details"
        }

        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        time.sleep(0.5)

        # We verify the values
        self.assertEqual(file.get("progress", 0), 100)
        self.assertEqual(file.get("status", FileStatus.FileAnalysing), FileStatus.FileInfected)

        # We send a delete file notification
        self.__nb_expected_messages = 1
        self.__message_event.clear()
        self.__messages_recv.clear()
        notif = NotificationFactory.create_notification_deleted_file(Constants.STR_REPOSITORY, "/.DS_Store")
        self.__mqtt_client.publish(Topics.DELETED_FILE, notif)

        time.sleep(0.2)

        self.assertEqual(self.__analysis_controller.get_repository_size(), 0)

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
        time.sleep(1)

        # We verify the values
        file = self.__files_queue.get("/Test.pdf", {})
        self.assertEqual(file.get("progress", 0), 100)
        self.assertEqual(file.get("locked", None), True)
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

    def test_scan_mixed_content(self):
        # Verify subscriptions
        self.assertTrue(self.__ready)

        # Wait for the init message
        self.__message_event.clear()
        self.__nb_expected_messages = 1
        self.assertTrue(self.__message_event.wait(1))
        self.assertEqual(len(self.__messages_recv), 1)

        # Update the queue with an archive
        #self.__update_queue([{"type": "file", "path": "/", "name": "File.txt", "size": 12345}, {"type": "file", "path": "/", "name": "Test.iso", "size": 50000000}])
        self.__update_queue(deepcopy(self.STORAGE_MIXED_FILES.get("files")))

        self.__messages_recv.clear()
        self.__message_event.clear()
        self.__nb_expected_messages = 3
        self.__analysis_controller.start_analysis()
        self.assertEqual(self.__analysis_controller.get_analysis_state(), AnalysisState.AnalysisRunning)
        # Wait for the Analysis/resume message
        self.assertTrue(self.__message_event.wait(2))

        # Verify the message received
        self.assertEqual(len(self.__messages_recv), 3)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/resume")
        self.assertEqual(self.__messages_recv[1]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[1]["payload"], {"disk": "Archives", "filepath": "/File.txt"})
        self.assertEqual(self.__messages_recv[2]["topic"], f"{Topics.READ_FILE}/request")
        self.assertEqual(self.__messages_recv[2]["payload"], {"disk": "Archives", "filepath": "/File2.txt"})

        # Reply...
        self.__messages_recv.clear()
        self.__nb_expected_messages = 1
        self.__message_event.clear()
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/File.txt", "abcdef0123456789", "abcdef0123456789")
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)
        # Wait for the analysis request
        self.__message_event.wait(0.5)        
        
        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"filepath": "/File.txt"})

        # Send the results
        self.__messages_recv.clear()
        self.__message_event.clear()                
        self.__nb_expected_messages = 1
        payload = { "component": "av1", "filepath": "/File.txt", "success": True, "details": "Some details" }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)
        payload = { "component": "av2", "filepath": "/File.txt", "success": True, "details": "Some details" }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # The controller should not begin with the archives unless the files
        # before have finished with the single files
        self.assertFalse(self.__message_event.wait(0.5))

        # Send the notifications for the second file
        self.__messages_recv.clear()
        self.__message_event.clear()                
        self.__nb_expected_messages = 1
        payload = NotificationFactory.create_notification_new_file(Constants.STR_REPOSITORY, "/File2.txt", "abcdef0123456789", "abcdef0123456789")
        self.__mqtt_client.publish(Topics.NEW_FILE, payload)        

        # We expect an analysis request
        self.assertTrue(self.__message_event.wait(0.5))
        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{TOPIC_ANALYSIS}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"filepath": "/File2.txt"})

        # Then we send the results
        self.__messages_recv.clear()
        self.__message_event.clear()                
        self.__nb_expected_messages = 1
        payload = { "component": "av1", "filepath": "/File2.txt", "success": True, "details": "Some details" }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)
        payload = { "component": "av2", "filepath": "/File2.txt", "success": True, "details": "Some details" }
        self.__mqtt_client.publish(f"{TOPIC_ANALYSIS}/response", payload)

        # We send deleted file notifications
        notif = NotificationFactory.create_notification_deleted_file(Constants.STR_REPOSITORY, "File.txt")
        self.__mqtt_client.publish(Topics.DELETED_FILE, notif)
        notif = NotificationFactory.create_notification_deleted_file(Constants.STR_REPOSITORY, "File2.txt")
        self.__mqtt_client.publish(Topics.DELETED_FILE, notif)

        # Wait for a request for the next file (the archive)
        self.assertTrue(self.__message_event.wait(2))

        # Verify the message received 
        self.assertEqual(len(self.__messages_recv), 1)
        self.assertEqual(self.__messages_recv[0]["topic"], f"{Topics.MOUNT_FILE}/request")
        self.assertEqual(self.__messages_recv[0]["payload"], {"disk": "Archives", "filepath": "/Test.iso"})

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
        file["locked"] = True

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(1)
        self.assertEqual(len(files), 1)

        file = files[0]
        self.assertEqual(file["name"], "Test.pdf")
        file["locked"] = True

        f = queue[0]
        f["status"] = FileStatus.FileAnalysing
        f = queue[1]
        f["status"] = FileStatus.FileAnalysing
        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(2)        
        self.assertEqual(len(files), 0)

        # Now we test mixed content
        queue = deepcopy(self.STORAGE_MIXED_FILES.get("files", []))
        self.__update_queue(queue)

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        self.assertEqual(len(files), 2) # We should only contain the 2 single files
        self.assertEqual(files[0].get("name", ""), "File.txt")
        self.assertEqual(files[1].get("name", ""), "File2.txt")

        # We set the status of these 2 files
        files[0]["status"] = FileStatus.FileAnalysing
        files[0]["locked"] = True
        files[1]["status"] = FileStatus.FileAnalysing
        files[1]["locked"] = True

        self.__analysis_controller._AnalysisController__repository_size = 2

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        print(files)
        self.assertEqual(len(files), 0) # The group should be empty

        # We set the status of the 2 files to finished
        queue[0]["status"] = FileStatus.FileClean
        queue[0]["progress"] = 100.0
        queue[2]["status"] = FileStatus.FileInfected
        queue[2]["progress"] = 100.0

        self.__analysis_controller._AnalysisController__repository_size = 0

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        self.assertEqual(len(files), 1) # The group should only contain the next archive
        self.assertEqual(files[0].get("name", ""), "Test.iso")
        
        files[0]["locked"] = True
        files[0]["status"] = FileStatus.FileAnalysing

        self.__analysis_controller._AnalysisController__repository_size = 1

        # We provide some content for the archive Test.iso
        archive_files = {
            "content": {
                "/File1.txt": { "name": "File1.txt", "path": "/" },
                "/File2.txt": { "name": "File2.txt", "path": "/" }
            }
        }
        self.__analysis_controller._AnalysisController__archive_mounted_name = "Test.iso"
        self.__analysis_controller._AnalysisController__archive_file = archive_files

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        self.assertEqual(len(files), 2) # This should be the content of the archive

        # Set the files finished
        archive_files["content"]["/File1.txt"]["progress"] = 100
        archive_files["content"]["/File1.txt"]["locked"] = True
        archive_files["content"]["/File2.txt"]["progress"] = 100
        archive_files["content"]["/File2.txt"]["locked"] = True

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        self.assertEqual(len(files), 0) # The group should be empty

        # Mark the archive finished
        queue[1]["status"] = FileStatus.FileClean
        queue[1]["progress"] = 100.0
        queue[1]["locked"] = True
        self.__analysis_controller._AnalysisController__archive_mounted_name = None
        self.__analysis_controller._AnalysisController__archive_mounted_filepath = None
        self.__analysis_controller._AnalysisController__archive_file = {}
        self.__analysis_controller._AnalysisController__repository_size = 0

        files = self.__analysis_controller._AnalysisController__get_next_group_of_files(10)
        self.assertEqual(len(files), 1) # The group should only contain the next archive
        self.assertEqual(files[0].get("name", ""), "Test2.iso")
        
        
    def test_reset(self):
        self.__analysis_controller.reset()
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_size(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_size(), 0)

    def test_handle_result_simple_files(self):
        self.__update_queue(self.STORAGE_FILES.get("files", []))

        self.assertEqual(self.__analysis_controller.get_queue_size(), 2)

        spyFileUpdated = QSignalSpy(self.__analysis_controller.fileUpdated)
        spyIterationDone = QSignalSpy(self.__analysis_controller.iterationDone)
        spyResultsChanged = QSignalSpy(self.__analysis_controller.resultsChanged)

        # The first analysis
        self.__analysis_controller._AnalysisController__handle_result("av1", "/.DS_Store", True, "")

        self.assertEqual(spyFileUpdated.count(), 1)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # The second analysis
        self.__analysis_controller._AnalysisController__handle_result("av2", "/.DS_Store", True, "")


        self.assertEqual(spyFileUpdated.count(), 2)
        self.assertEqual(spyIterationDone.count(), 1)
        self.assertEqual(spyResultsChanged.count(), 1)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 1)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # Next files
        # The first analysis
        self.__analysis_controller._AnalysisController__handle_result("av1", "/Test.pdf", False, "")

        self.assertEqual(spyFileUpdated.count(), 3)
        self.assertEqual(spyIterationDone.count(), 1)
        self.assertEqual(spyResultsChanged.count(), 1)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 1)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # The second analysis
        self.__analysis_controller._AnalysisController__handle_result("av2", "/Test.pdf", True, "")

        self.assertEqual(spyFileUpdated.count(), 4)
        self.assertEqual(spyIterationDone.count(), 2)
        self.assertEqual(spyResultsChanged.count(), 2)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 1)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 1)

    def test_handle_result_archive(self):
        self.__update_queue(self.ARCHIVE_FILES)
        content = {}
        for f in self.ARCHIVE_FILES:
            content[f"{f["path"]}/{f["name"]}"] = f

        self.__analysis_controller._AnalysisController__archive_mounted_name = "Test.iso"
        self.__analysis_controller._AnalysisController__archive_mounted_filepath = "/Test.iso"
        self.__analysis_controller._AnalysisController__archive_file = { "name": "Test.iso", "path": "/", "size": 50000000, "inqueue": True, "content": content }
        self.assertEqual(self.__analysis_controller.get_queue_size(), 4)
        
        spyFileUpdated = QSignalSpy(self.__analysis_controller.fileUpdated)
        spyIterationDone = QSignalSpy(self.__analysis_controller.iterationDone)
        spyResultsChanged = QSignalSpy(self.__analysis_controller.resultsChanged)

        # File 1 - analysis 1
        self.__analysis_controller._AnalysisController__handle_result("av1", "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp", True, "")

        self.assertEqual(spyFileUpdated.count(), 1)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 1 - analysis 2
        self.__analysis_controller._AnalysisController__handle_result("av2", "/1.3.0/atmosphere/contents/4200000000003103/exefs.nsp", True, "")

        self.assertEqual(spyFileUpdated.count(), 2)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 2 - analysis 1
        self.__analysis_controller._AnalysisController__handle_result("av1", "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag", True, "")

        self.assertEqual(spyFileUpdated.count(), 3)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 2 - analysis 2
        self.__analysis_controller._AnalysisController__handle_result("av2", "/1.3.0/atmosphere/contents/4200000000003103/flags/boot2.flag", False, "")

        self.assertEqual(spyFileUpdated.count(), 4)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 3 - analysis 1
        self.__analysis_controller._AnalysisController__handle_result("av1", "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json", True, "")

        self.assertEqual(spyFileUpdated.count(), 5)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 3 - analysis 2
        self.__analysis_controller._AnalysisController__handle_result("av2", "/1.3.0/atmosphere/contents/4200000000003103/toolbox.json", True, "")

        self.assertEqual(spyFileUpdated.count(), 6)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 4 - analysis 1
        self.__analysis_controller._AnalysisController__handle_result("av1", "/1.3.0/switch/.overlays/parental_control.ovl", True, "")

        self.assertEqual(spyFileUpdated.count(), 7)
        self.assertEqual(spyIterationDone.count(), 0)
        self.assertEqual(spyResultsChanged.count(), 0)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 0)

        # File 4 - analysis 2
        self.__analysis_controller._AnalysisController__handle_result("av2", "/1.3.0/switch/.overlays/parental_control.ovl", True, "")

        # We receive 2 updates at the end of the archive analysis
        self.assertEqual(spyFileUpdated.count(), 9)
        self.assertEqual(spyIterationDone.count(), 1)
        self.assertEqual(spyResultsChanged.count(), 1)
        self.assertEqual(self.__analysis_controller.get_clean_files_count(), 0)
        self.assertEqual(self.__analysis_controller.get_infected_files_count(), 1)


    def test_get_working_files_count(self):
        self.__files_queue.clear()

        self.__files_queue["/1"] = { "status": FileStatus.FileStatusUndefined }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 0)

        self.__files_queue["/1"] = { "status": FileStatus.FileAnalysing }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 1)

        self.__files_queue["/1"] = { "status": FileStatus.FileAnalysisError }
        self.__files_queue["/2"] = { "status": FileStatus.FileAnalysing }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 1)

        self.__files_queue["/1"] = { "status": FileStatus.FileAvailableInRepository }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 1)

        self.__files_queue["/1"] = { "status": FileStatus.FileClean }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 0)

        self.__files_queue["/1"] = { "status": FileStatus.FileClean }
        self.__files_queue["/2"] = { "status": FileStatus.FileAnalysing }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 1)

        self.__files_queue["/1"] = { "status": FileStatus.FileCopyError }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 0)

        self.__files_queue["/1"] = { "status": FileStatus.FileCopySuccess }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 1)

        self.__files_queue["/1"] = { "status": FileStatus.FileInfected }
        self.__files_queue["/2"] = { "status": FileStatus.FileStatusUndefined }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 0)

        self.__files_queue["/1"] = { "status": FileStatus.FileInfected }
        self.__files_queue["/2"] = { "status": FileStatus.FileClean }
        self.assertEqual(self.__analysis_controller.get_working_files_count(), 0)

    def __update_queue(self, files_list:list[dict]):
        self.__files_queue.clear()

        for f in files_list:
            filepath = f"{"" if f.get("path") == "/" else f.get("path")}/{f.get("name")}"
            f["filepath"] = filepath
            f["inqueue"] = True
            self.__files_queue[filepath] = f
