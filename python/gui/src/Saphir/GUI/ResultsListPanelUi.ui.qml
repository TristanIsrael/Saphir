import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

Rectangle {
    id: root

    property int globalProgress: 0
    property alias tblView: tblView
    property alias model: tblView.model
    property alias pnlDigits: pnlDigits

    color: Constants.contrastColor
    implicitHeight: 500
    implicitWidth: 400

    Rectangle {
        id: entete
        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }
        implicitHeight: 50

        color: Constants.headingColor

        RowLayout {
            anchors.centerIn: parent

            Icone {
                id: icnUsb
                text: "\ue05f" //f02f, e6b3, e241
                color: Constants.contrastColor
            }

            PText {
                id: lblDriveName
                text: globalProgress > 0 ? qsTr("Analyse en cours (%1 %)").arg(
                                               globalProgress) : qsTr(
                                               "Aucune analyse en cours")
                color: Constants.contrastColor
            }
        }
    }

    TableView {
        id: tblView

        model: ApplicationController.queueListModel

        clip: true
        anchors {
            top: entete.bottom
            left: parent.left
            right: parent.right
            bottom: pnlDigits.top
            margins: 10
        }

        //visible: globalProgress > 0
        rowSpacing: 0

        delegate: Rectangle {
            implicitWidth: tblView.width
            //implicitHeight: type === "file" && progress < 100 ? 40 : 0.00001
            implicitHeight: progress < 100 ? 40 : 0.00001

            Rectangle {
                implicitHeight: parent.height
                implicitWidth: parent.width * (progress / 100)
                color: progress === 100 ? infected ? Constants.alertColor : Constants.successColor : Constants.progressColor
            }

            PText {
                text: filepath
                level: PText.TextLevel.Paragraph
                color: progress === 100 ? Constants.contrastColor : Constants.textColor
                elide: Text.ElideMiddle

                anchors {
                    left: parent.left
                    leftMargin: 10
                    top: parent.top
                    bottom: parent.bottom
                    right: parent.right
                    rightMargin: 10
                }
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    ResultDigitsPanel {
        id: pnlDigits

        height: parent.width / 6
        anchors {
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }

        //visible: globalProgress > 0        
        infected: 0
        clean: 0
        total: root.tblView.rows
    }
}
