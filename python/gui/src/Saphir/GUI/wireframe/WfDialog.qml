import QtQuick
import QtQuick.Layouts
import Components

WfPanel {
    id: root

    property alias label: txt.text
    property list<string> buttonsLabels: [ "Ok", "Cancel"]

    width: implicitWidth
    height: implicitHeight
    implicitWidth: Environment.mainWidth/3
    implicitHeight: Environment.mainHeight/3

    WfText {
        id: txt
        anchors.centerIn: parent
        text: "Message dialog"
        color: Environment.colorText
    }

    RowLayout {
        anchors {
            bottom: parent.bottom
            bottomMargin: 20
            left: parent.left
            right: parent.right
        }

        height: 30

        Item { Layout.fillWidth: true }

        Repeater {
            model: buttonsLabels

            WfButton {
                label: modelData
            }
        }

        Item { Layout.fillWidth: true }
    }
}
