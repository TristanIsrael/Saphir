import QtQuick
import Components
import Saphir

Item {
    id: root

    /* Bindings */
    property bool handheld: ApplicationController.handheld
    property bool ready: ApplicationController.ready    
    property int batteryLevel: ApplicationController.batteryLevel
    property bool plugged: ApplicationController.plugged
    property bool ambientLightSensorReady: false
    property int ambientLight: 0 // 0 (dark) - 100 (sunny)
    property int classificationLevel: 0 // to map with an enumeration
    property var disksList: ApplicationController.disks
    property string currentFolder: ApplicationController.currentFolder
    property string currentDisk: ApplicationController.currentDisk
    property bool sourceReady: ApplicationController.sourceReady
    property string currentStep: ApplicationController.currentStep
    property string currentFilepath: ApplicationController.currentFilepath
    property string repositoryPath: ApplicationController.repositoryPath
    property int currentFiletype: ApplicationController.currentFiletype
    
    /** Models */
    property var inputFilesListModel: ApplicationController.inputFilesListModel
    //property var inputFilesListProxyModel: ApplicationController.inputFilesListProxyModel
    
    /* System states */
    readonly property color systemStateColor: {
        if(!bindings.ready) {
            return Environment.colorFilterNotReady
        } else {
            if(bindings.infected) {
                return Environment.colorFilterInfected
            } else if(bindings.used) {
                return Environment.colorFilterUsed
            }
        }

        return Environment.colorFilterReady
    }

    /* Functions */
    function updateSourceFilesList() {
        ApplicationController.update_source_files_list()
    }

    function goToParentFolder() {
        ApplicationController.go_to_parent_folder()
    }

    function goToFolder(folder) {
        ApplicationController.go_to_folder(folder)
    }

    function reset() {
        ApplicationController.reset()
    }

    function shutdown() {
        ApplicationController.shutdown()
    }

    function viewFile(filepath) {
        ApplicationController.view_file(filepath)
    }

    function clearCurrentFile() {
        ApplicationController.clear_current_file()
    }

    function on_disk_selected(disk_name) {
        ApplicationController.on_disk_selected(comboStorages.currentValue)
    }

    function back_to_saphir() {
        ApplicationController.back_to_saphir()
    }

    /**
        For development only
    */
    ListModel {
        id: debugMessages
    }

    ListModel {
        id:debugSourceListModel

        ListElement {
            type: "folder"
            filepath: "/"
            filename: "Folder 1"
            selected: false
        }

        ListElement {
            type: "file"
            filepath: "/Folder 1"
            filename: "File 1"
            selected: false
            progress: 32
            status: 0
        }

        ListElement {
            type: "file"
            filepath: "/"
            filename: "File 1"
            selected: false
            progress: 85
            status: 0
        }
    }

    Timer {
        repeat: true
        interval: 1000

        running: false
        onTriggered: {
            root.debugMessages.append({"text": "Bla bla bla" + Math.random()})
        }
    }

}
