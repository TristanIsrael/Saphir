import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../imports"

Rectangle {
    id: root

    property string libelle: "Voulez-vous analyser l'intégralité du support ?"

    signal accepted()
    signal rejected()

    implicitWidth: 500
    implicitHeight: 300

    border {
        color: "#505a6d"
        width: 4
    }

    color: "#606b81"

    ColumnLayout {
        id: lyt

        anchors {
            fill: parent
            margins: 20
        }

        Item {
            Layout.fillHeight: true
        }

        Label {
            id: lblLibelle
            color: Constants.colorText
            text: root.libelle
            font.pixelSize: 20
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
        }

        Item {
            Layout.fillHeight: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            spacing: 100

            Item {
                Layout.fillWidth: true
            }

            Rectangle {
                color: "transparent"
                Layout.preferredWidth: 70
                Layout.preferredHeight: parent.height

                border {
                    width: 3
                    color: "#505a6d"
                }

                Label {
                    id: lblOui
                    anchors.fill: parent
                    text: "Oui"
                    font.pixelSize: 20

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: Constants.colorText

                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.accepted()
                    }
                }
            }

            Rectangle {
                color: "transparent" //Constants.colorBlue
                Layout.preferredWidth: 70
                Layout.preferredHeight: parent.height

                border {
                    width: 3
                    color: "#505a6d"
                }

                Label {
                    id: lblNon
                    anchors.fill: parent
                    text: "Non"
                    font.pixelSize: 20

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    color: Constants.colorBlue

                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.rejected()
                    }
                }
            }

            Item {
                Layout.fillWidth: true
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
