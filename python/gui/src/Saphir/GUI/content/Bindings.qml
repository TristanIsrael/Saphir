import QtQuick
import Components

Item {
    id: root

    /* Bindings */
    property bool ready: true
    property bool running: true
    property bool infected: false
    property bool used: false
    property string sourceName: "Untitled in"
    property string targetName: "Untitled out"
    property bool ambientLightSensorReady: true
    property int ambientLight: 100 // 0 (dark) - 100 (sunny)
    property int classificationLevel: 0 // to map with an enumeration
    property string currentFolder: "/Folder 1"
    property int nbClean: 1052
    property int nbInfected: 5012
    property int nbWaiting: 10120

    /** Models */
    property var sourceFilesListModel: ListModel {
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

    property alias messages: messages
    //property ListModel messages

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
    function goToParentFolder() {
        console.debug("goToParentFolder() called")
    }

    function goToFolder(folder) {
        console.debug("goToFolder(", folder, ") called")
    }

    function addToQueue(type, filepath) {
        console.debug("addToQueue(", type ,", ", filepath, ") called")
    }

    function removeFromQueue(type, filepath) {
        console.debug("removeFromQueue(", type ,", ", filepath, ") called")
    }

    /**
        For development only
    */
    ListModel {
        id: messages
    }

    Timer {
        repeat: true
        interval: 1000

        running: false
        onTriggered: {
            root.messages.append({"text": "Bla bla bla" + Math.random()})
        }
    }

}
