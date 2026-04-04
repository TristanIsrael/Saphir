import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import QtQuick.Controls
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

    Button {
        id: icnBattery
        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }

        flat: true
        padding: 0
        width: 30
        icon.height: height

        icon.color: root.color
        icon.source: {
            if(bindings.batteryLevel > 75) {
                return "images/battery_android_full_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            } else if(bindings.batteryLevel > 60) {
                return "images/battery_android_6_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            } else if(bindings.batteryLevel > 45) {
                return "images/battery_android_5_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            } else if(bindings.batteryLevel > 30) {
                return "images/battery_android_4_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            } else if(bindings.batteryLevel > 15) {
                return "images/battery_android_3_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            } else if(bindings.batteryLevel > 5) {
                return "images/battery_android_2_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            }
            return "images/battery_android_alert_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
        }
    }


    Bindings {
        id: bindings
    }
}
