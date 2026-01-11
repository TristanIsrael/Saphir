import QtQuick
import Components
import Saphir

Item {
    id: root

    /* Bindings */
    property bool ready: ApplicationController.ready
    property bool analysisReady: ApplicationController.analysisReady 
    property bool running: false
    property bool infected: false
    property bool used: false
    property string sourceName: ApplicationController.sourceName
    property string targetName: ApplicationController.targetName
    property bool ambientLightSensorReady: false
    property int ambientLight: 0 // 0 (dark) - 100 (sunny)
    property int classificationLevel: 0 // to map with an enumeration
    property string currentFolder: ApplicationController.currentFolder
    property int nbClean: ApplicationController.cleanFilesCount
    property int nbInfected: ApplicationController.infectedFilesCount
    property int nbAnalyzing: ApplicationController.analysingCount
    property int nbWaiting: ApplicationController.queueSize - (ApplicationController.cleanFilesCount + ApplicationController.infectedFilesCount + ApplicationController.analysingCount)
    property int queueSize: ApplicationController.queueSize

    /** Models */
    property var sourceFilesListModel: ApplicationController.inputFilesListProxyModel

    property var messages: ApplicationController.messagesListModel

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
    function setAnalysisMode(mode) {
        ApplicationController.analysisMode = mode
    }

    function updateSourceFilesList() {
        ApplicationController.update_source_files_list()
    }

    function goToParentFolder() {
        console.debug("goToParentFolder() called")
        ApplicationController.go_to_parent_folder()
    }

    function goToFolder(folder) {
        console.debug("goToFolder(", folder, ") called")
        ApplicationController.go_to_folder(folder)
    }

    function addToQueue(type, filepath) {
        console.debug("addToQueue(", type ,", ", filepath, ") called")
        ApplicationController.enqueue_file(type, filepath)
    }

    function removeFromQueue(type, filepath) {
        console.debug("removeFromQueue(", type ,", ", filepath, ") called")
        ApplicationController.dequeue_file(filepath)
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
