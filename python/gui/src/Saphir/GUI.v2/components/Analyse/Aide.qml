import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"

Item {
    id: coreHelper    

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath  + "Modale.svg")
        width: parent.width
        height: parent.height
        fillMode: Image.Stretch
        anchors.fill: parent
    }

    Image {
        id: returnButton
        source: Qt.resolvedUrl(Constants.colorModePath  + "FermerModale.svg")
        height: parent.height * 0.12
        width: parent.width * 0.075
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: (parent.width * 0.02) + (width * 0.5)
        MouseArea {
            anchors.fill: parent
            onClicked: coreHelper.visible = !coreHelper.visible
        }
    }

    Rectangle {
        id: modalContentContainer
        anchors.centerIn: parent
        width: parent.width * 0.96
        height: parent.height * 0.85
        anchors.verticalCenterOffset: parent.height * -0.05
        color: "transparent"
    }

    ColumnLayout {
        anchors.fill: modalContentContainer
        Rectangle {
            Layout.preferredHeight: 25
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            Rectangle {
                id: modalTitleHolder
                anchors.left: parent.left
                height: parent.height
                width: parent.width * 0.5
                color: "transparent"
                border.width: width * 0.01
                border.color: "white"
                radius: width * 0.05
                Label {
                    id: modalTitleText
                    anchors.centerIn: parent
                    width: parent.width - (parent.border.width * 3)
                    height: parent.height - (parent.border.width * 3)
                    text: "SUGGESTIONS"
                    color: "white"
                    font.pixelSize: width * 0.1
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Item {
            //Spacer
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        ColumnLayout {
            Layout.preferredHeight: 75
            Layout.fillHeight: true
            Layout.fillWidth: true

            Row {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                Item {
                    height: parent.height
                    width: parent.width * 0.2
                    Image {
                        source: Qt.resolvedUrl(Constants.colorModePath  + "PlayActif.svg")
                        width:parent.width
                        height:parent.height
                        fillMode: Image.PreserveAspectFit
                        anchors.right: parent.right

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {}
                        }
                    }
                }
                Label {
                    height: parent.height
                    width: parent.width * 0.8

                    text: "Passer en heure locale"
                    color: "white"
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Row {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                Item {
                    height: parent.height
                    width: parent.width * 0.2
                    Image {
                        source: Qt.resolvedUrl(Constants.colorModePath  + "PlayActif.svg")
                        width:parent.width
                        height:parent.height
                        fillMode: Image.PreserveAspectFit
                        anchors.right: parent.right

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {}
                        }
                    }
                }
                Label {
                    height: parent.height
                    width: parent.width * 0.8

                    text: "Passer en mode manuel"
                    color: "white"
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Row {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                Item {
                    height: parent.height
                    width: parent.width * 0.2
                    Image {
                        source: Qt.resolvedUrl(Constants.colorModePath  + "PlayActif.svg")
                        width:parent.width
                        height:parent.height
                        fillMode: Image.PreserveAspectFit
                        anchors.right: parent.right

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {}
                        }
                    }
                }
                Label {
                    height: parent.height
                    width: parent.width * 0.8

                    text: "Arrêter le scan des fichiers"
                    color: "white"
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Row {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                Item {
                    height: parent.height
                    width: parent.width * 0.2
                    Image {
                        source: Qt.resolvedUrl(Constants.colorModePath  + "PlayActif.svg")
                        width: parent.width
                        height: parent.height
                        fillMode: Image.PreserveAspectFit
                        anchors.right: parent.right

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {}
                        }
                    }
                }
                Label {
                    height: parent.height
                    width: parent.width * 0.8

                    text: "Transfert des fichiers"
                    color: "white"
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Item {
            //Spacer
            Layout.preferredHeight: 10
            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}
