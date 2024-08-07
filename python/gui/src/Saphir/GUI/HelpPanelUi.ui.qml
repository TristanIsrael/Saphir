import QtQuick
import QtQuick.Layouts
//import QtQuick.Effects
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property alias title: lblTitle.text
    property alias comment: lblComment.text

    width: implicitWidth
    implicitWidth: 300
    height: implicitHeight
    implicitHeight: lyt.height + 16

    Rectangle {
        id: bkg
        anchors.fill: parent
        color: Constants.popupBackgroundColor
        opacity: 0.9
        radius: height / 10
    }

    ColumnLayout {
        id: lyt

        y: 8
        anchors {
            left: parent.left
            right: parent.right
            margins: 8
        }

        PText {
            id: lblTitle
            Layout.preferredWidth: parent.width

            //text: qsTr("Title")
            color: Constants.contrastColor
            horizontalAlignment: Text.AlignHCenter
            level: PText.TextLevel.H4
            visible: text !== ""
        }

        PText {
            id: lblComment
            Layout.preferredWidth: parent.width

            text: qsTr(
                      "An explanation to help the user understand what is supposed to happen here.")
            color: Constants.contrastColor
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
        }
    }
}
