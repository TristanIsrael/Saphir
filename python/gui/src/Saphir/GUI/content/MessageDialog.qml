import QtQuick
import QtQuick.Layouts
import Components

PanelBase {
    id: root

    objectName: "dialog"
    property alias label: txt.text
    property list<string> buttonsLabels: [ "Ok", "Cancel"]

    width: implicitWidth
    height: implicitHeight
    implicitWidth: Environment.mainWidth/3
    implicitHeight: Environment.mainHeight/3
    radius: 10

    Text {
        id: txt
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            bottom: lyt.top
        }

        text: "Message dialog"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: Environment.colorText
        font.pixelSize: lyt.height *0.5
        fontSizeMode: Text.HorizontalFit
    }

    RowLayout {
        id: lyt

        anchors {
            bottom: parent.bottom
            bottomMargin: 20
            left: parent.left
            right: parent.right
        }

        Item { Layout.fillWidth: true }

        Repeater {
            id: rpt
            model: buttonsLabels

            Rectangle {
                width: 100
                height: 50

                color: "transparent"
                border {
                    width: 2
                    color: "#fafafa"
                }

                Text {
                    anchors.fill: parent
                    text: modelData
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: parent.height * 0.4
                    font.capitalization: Font.SmallCaps
                }
            }
        }

        Item { Layout.fillWidth: true }
    }
}
