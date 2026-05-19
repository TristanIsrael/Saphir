import QtQuick
import Components

PanelBase {
    id: root

    property real progress: bindings.systemLoadingProgress

    implicitWidth: Environment.mainWidth * 0.5
    implicitHeight: Environment.mainHeight * 0.2
    radius: 10

    Item {
        id: wrapper
        width: parent.width
        height: parent.height/2
        y: (parent.height - height) /2
        clip: true

        Rectangle {
            id: rctProgress

            x: rctBegin.x + rctBegin.width/2
            y: rctBegin.y + rctBegin.height/2 - height/2
            z: 0.1

            height: 5
            width: rctReady.x * progress
            color: Environment.colorRunning.alpha(0.25)
        }

        StyledText {
            text: qsTr("GUI\nready")
            horizontalAlignment: Qt.AlignHCenter
            x: rctBegin.x
            width: rctBegin.width
        }

        Circle {
            id: rctBegin

            y: parent.height - height
            z: 0.2
            height: 30
            borderWidth: 2
            borderColor: Environment.colorDark
            color: Environment.colorClean
        }

        StyledText {
            text: qsTr("Core\nready")
            horizontalAlignment: Qt.AlignHCenter
            x: rctStateCore.x
            width: rctStateCore.width
        }

        Circle {
            id: rctStateCore
            x: (parent.width-width)/3
            y: parent.height - height
            z: 0.2
            height: 30
            borderWidth: 2
            borderColor: Environment.colorDark
            color: progress >= 0.33 ? Environment.colorClean : Environment.colorWaiting
        }

        StyledText {
            text: qsTr("Antiviruses\nready")
            horizontalAlignment: Qt.AlignHCenter
            x: rctStateAntiviruses.x
            width: rctStateAntiviruses.width
        }

        Circle {
            id: rctStateAntiviruses

            x: (parent.width-width)/3*2
            y: parent.height - height
            z: 0.2

            height: 30
            borderWidth: 2
            borderColor: Environment.colorDark
            color: progress >= 0.66 ? Environment.colorClean : Environment.colorWaiting
        }

        StyledText {
            text: qsTr("Saphir\nready")
            horizontalAlignment: Qt.AlignHCenter
            x: rctReady.x
            width: rctReady.width
        }

        Circle {
            id: rctReady

            x: parent.width-width
            y: parent.height - height
            z: 0.2

            height: 30
            borderWidth: 2
            borderColor: Environment.colorDark
            color: progress === 1 ? Environment.colorClean : Environment.colorWaiting
        }
    }

    Bindings {
        id: bindings
    }
}
