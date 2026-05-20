import QtQuick
import Components
import Saphir

PanelBase {
    id: root

    property real progress: bindings.systemLoadingProgress
    property bool big: height > 100
    property bool resetting: bindings.systemState === Enums.SystemResetting

    implicitWidth: Environment.mainWidth * 0.5
    implicitHeight: Environment.mainHeight * 0.2
    radius: 10
    visible: opacity > 0

    StyledText {
        text: root.resetting ? qsTr("Cleaning...") : qsTr("Starting...")
        anchors.horizontalCenter: parent.horizontalCenter
        y: 5
        section: root.big ? Constants.Section.Paragraph : Constants.Section.SuperTiny
    }

    Item {
        id: wrapper
        width: parent.width
        height: root.big ? parent.height/2 : parent.height*0.8
        y: (parent.height - height) /2
        clip: true

        Rectangle {
            id: rctProgress

            x: rctBegin.x + rctBegin.width/2
            y: rctBegin.y + rctBegin.height/2 - height/2
            z: 0.1

            height: root.big ? 5 : 2.5
            width: rctReady.x * root.progress
            color: Environment.colorClear.alpha(0.75)

            Behavior on width {
                NumberAnimation {
                    easing.type: Easing.InOutCubic
                    duration: 1500
                }
            }
        }

        StyledText {
            text: qsTr("GUI")
            horizontalAlignment: Qt.AlignHCenter
            x: rctBegin.x
            width: rctBegin.width
            height: parent.height - rctBegin.height - 5
            verticalAlignment: Text.AlignBottom
            section: root.big ? Constants.Section.Paragraph : Constants.Section.SuperTiny
        }

        Circle {
            id: rctBegin

            y: parent.height - height
            z: 0.2
            height: root.big ? 30 : 15
            borderWidth: 2
            borderColor: Environment.colorDark
            color: Environment.colorClean
        }

        StyledText {
            text: qsTr("Core")
            horizontalAlignment: Qt.AlignHCenter
            x: rctStateCore.x
            width: rctStateCore.width
            height: parent.height - rctBegin.height - 5
            verticalAlignment: Text.AlignBottom
            section: root.big ? Constants.Section.Paragraph : Constants.Section.SuperTiny
        }

        Circle {
            id: rctStateCore
            x: (parent.width-width)/3
            y: parent.height - height
            z: 0.2
            height: root.big ? 30 : 15
            borderWidth: 2
            borderColor: Environment.colorDark
            color: root.progress >= 0.33 ? Environment.colorClean : Environment.colorWaiting
        }

        StyledText {
            text: qsTr("Antiviruses")
            horizontalAlignment: Qt.AlignHCenter
            x: rctStateAntiviruses.x
            width: rctStateAntiviruses.width
            height: parent.height - rctBegin.height - 5
            verticalAlignment: Text.AlignBottom
            section: root.big ? Constants.Section.Paragraph : Constants.Section.SuperTiny
        }

        Circle {
            id: rctStateAntiviruses

            x: (parent.width-width)/3*2
            y: parent.height - height
            z: 0.2

            height: root.big ? 30 : 15
            borderWidth: 2
            borderColor: Environment.colorDark
            color: root.progress >= 0.66 ? Environment.colorClean : Environment.colorWaiting
        }

        StyledText {
            text: qsTr("Complete")
            horizontalAlignment: Qt.AlignHCenter
            x: rctReady.x
            width: rctReady.width
            height: parent.height - rctBegin.height - 5
            verticalAlignment: Text.AlignBottom
            section: root.big ? Constants.Section.Paragraph : Constants.Section.SuperTiny
        }

        Circle {
            id: rctReady

            x: parent.width-width
            y: parent.height - height
            z: 0.2

            height: root.big ? 30 : 15
            borderWidth: 2
            borderColor: Environment.colorDark
            color: root.progress === 1 ? Environment.colorClean : Environment.colorWaiting
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: 1000
        }
    }

    Bindings {
        id: bindings
    }

    // Slots
    onProgressChanged: function() {
        rctProgress.width = rctReady.x * progress
    }

    Component.onCompleted: function() {
        rctProgress.width = rctReady.x * progress
    }    

}
