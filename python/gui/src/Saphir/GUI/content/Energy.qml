import QtQuick
import QtQuick.Layouts
import Components

Item {
    id: root

    property color color: Environment.colorText

    height: implicitHeight
    implicitHeight: 28
    width: implicitWidth
    implicitWidth: icnPlugged.width + icnBattery.width + height*0.25


    Text {
        id: icnPlugged
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }

        font.family: "Material Icons Outlined"
        font.pixelSize: root.height
        text: "\ue63c"
        verticalAlignment: Qt.AlignVCenter
        color: root.color
    }

    Text {
        id: icnBattery
        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }

        font.family: "Material Symbols Outlined"
        font.pixelSize: root.implicitHeight
        verticalAlignment: Qt.AlignVCenter
        text: Constants.battery_0
        color: root.color
    }
}
