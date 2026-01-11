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

            onCountChanged: {
                const txt = itemAtIndex(count -1)
                if(txt !== null && txt.y > height) {
                    contentY = txt.y - height + txt.height
                }
            }

            delegate: Text {
                text: display
                color: Environment.colorText
                font.pixelSize: wrapper.height/(wrapper.lines+1)
            }

            Behavior on contentY {
                PropertyAnimation {
                    id: animateScroll
                    duration: 200
                }
            }

        }
    }

    Bindings {
        id: bindings
    }
}
