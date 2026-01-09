import QtQuick
import QtQuick.Layouts
import Components

RowLayout {
    id: root

    property color color: "white"

    implicitHeight: icnPlugged.height

    Text {
        id: icnPlugged
        font.family: "Material Icons Outlined"
        font.pixelSize: 28
        text: "\ue63c"
        color: root.color
    }

    Text {
        id: icnBattery
        font.family: "Material Symbols Outlined"
        font.pixelSize: 28
        text: Constants.battery_0
        color: root.color
    }
}
