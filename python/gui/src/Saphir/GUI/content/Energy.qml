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
        visible: bindings.plugged
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
        text: {
            if(bindings.batteryLevel > 75) {
                return Constants.battery_100
            } else if(bindings.batteryLevel > 60) {
                return Constants.battery_75
            } else if(bindings.batteryLevel > 45) {
                return Constants.battery_60
            } else if(bindings.batteryLevel > 30) {
                return Constants.battery_45
            } else if(bindings.batteryLevel > 15) {
                return Constants.battery_30
            } else if(bindings.batteryLevel > 5) {
                return Constants.battery_15
            }
            return Constants.battery_0
        }
        color: root.color
    }

    Bindings {
        id: bindings
    }
}
