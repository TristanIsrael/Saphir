import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property int marges: 16
    property bool principal: false
    property alias text: lbl.text
    property string icone: "\ue03b"

    implicitWidth: lbl.width + icn.width + marges * 2.5
    implicitHeight: lbl.height + marges

    color: principal ? Constants.buttonColor : Constants.contrastColor
    border {
        color: principal ? Constants.contrastColor : Constants.buttonColor
    }

    Icone {
        id: icn
        text: root.icone
        anchors {
            left: parent.left
            leftMargin: root.marges / 2
            verticalCenter: parent.verticalCenter
        }
    }

    PText {
        id: lbl
        anchors {
            verticalCenter: parent.verticalCenter
            left: icn.right
            leftMargin: root.marges / 1.3
        }

        font.pointSize: 18
        text: qsTr("Bouton d'action")
        color: principal ? Constants.contrastColor : Constants.buttonColor
    }
}
