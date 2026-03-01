import QtQuick
import Components

Rectangle {
    id: root

    property alias label: txt.text
    property bool noborder: false
    property bool outlined: true

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 60
    implicitHeight: 60

    color: "transparent"
    radius: height

    border {
        width: noborder ? 0 : 4
        color: Environment.colorBorder
    }

    Item {
        anchors.fill: parent
        anchors.margins: height*0.1

        Text {
            id: txt
            anchors.fill: parent
            font.family: outlined ? "Material Icons Outlined" : "Material Icons"
            text: Constants.iconHelp
            font.pixelSize: parent.height
        }
    }
}
