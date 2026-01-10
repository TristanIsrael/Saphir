import QtQuick
import Components

PanelBase {
    id: root

    implicitWidth: Environment.mainWidth * 0.5
    implicitHeight: Environment.mainHeight * 0.1

    Item {
        id: wrapper
        anchors.fill: parent
        clip: true

        readonly property int lines: 3

        ListView {
            id: listView

            anchors {
                fill: parent
                margins: parent.height * 0.1
            }

            model: bindings.messages

            delegate: Text {
                text: modelData
                color: Environment.colorText
                font.pixelSize: wrapper.height/(wrapper.lines+1)
            }

        }
    }

    Bindings {
        id: bindings
    }
}
