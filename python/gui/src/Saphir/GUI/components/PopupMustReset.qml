import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import "../imports"

Item {
    id: root
    property string libelle: "Le système doit être réinitialisé avant\nune nouvelle analyse."

    signal accepted()
    signal rejected()

    implicitWidth: 500
    implicitHeight: 300

    Item {
        anchors.fill: parent

        Item {
            anchors.fill: parent
        
            Rectangle {
                id: bkg
                anchors.fill: parent

                radius: 10
            }

            DropShadow {
                anchors.fill: bkg
                radius: 10
                color: Constants.colorRed
                source: bkg
                cached: true
            }
        }
    }

    Rectangle {
        anchors.fill: parent

        radius: bkg.radius
        border {
            color: "#505a6d"
            width: 4
        }

        color: Constants.currentColorMode === Constants.LIGHT ? "#eee" : Constants.currentColorMode === Constants.DARK ? "#606b81" : "#272727"

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
                    Layout.preferredWidth: 100
                    Layout.preferredHeight: parent.height

                    border {
                        width: 3
                        color: "#505a6d"
                    }

                    Label {
                        id: lblOui
                        anchors.fill: parent
                        text: "Fermer"
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

                Item {
                    Layout.fillWidth: true
                }
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }
}
