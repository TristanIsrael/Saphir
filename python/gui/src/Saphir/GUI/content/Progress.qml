import QtQuick
import Components

Item {
    id: root

    property int progress: 80

    width: implicitWidth
    height: implicitHeight
    implicitHeight: 20
    implicitWidth: 100

    Rectangle {
        anchors.fill: parent

        color: "transparent"
        border {
            width: 2
            color: Environment.colorBorder
        }

        Rectangle {
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
                margins: parent.border.width
            }

            color: "gray"
            width: parent.width * progress/100
        }

        Text {
            anchors.centerIn: parent
            text: progress +" %"
        }
    }
}
