import QtQuick
import Components

Item {
    id: root

    /* Bindings */
    property bool ready: true
    property bool running: false
    property bool infected: false
    property bool used: false
    property string sourceName
    property string targetName
    property alias messages: messages
    //property ListModel messages

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

    /* For development only */
    ListModel {
        id: messages
    }

    /* Functions */
    Timer {
        repeat: true
        interval: 1000

        running: true
        onTriggered: {
            root.messages.append({"text": "Bla bla bla" + Math.random()})
        }
    }

}
