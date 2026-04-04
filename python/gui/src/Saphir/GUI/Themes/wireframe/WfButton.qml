import QtQuick
import Components

Rectangle {
    property alias label: txt.text

    width: 120
    height: 36

    color: Environment.colorControl
    border {
        width: 2
        color: Environment.colorBorder
    }

    Text {
        id: txt
        anchors.centerIn: parent
        text: "Label"
        color: Environment.colorText
    }
}
