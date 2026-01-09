import QtQuick
import Components

Rectangle {
    id: root

    property bool checked: false

    implicitWidth: 30
    implicitHeight: 30

    border {
        color: Environment.colorBorder
        width: 2
    }

    WfText {
        anchors.centerIn: parent
        text: checked ? "\u2714" : ""
        font.pixelSize: height
    }
}
