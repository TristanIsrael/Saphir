import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"

Rectangle {
    id: coreEtatLogs
    color: "transparent"

    property ListModel _logsList
    property int maxItemDisplayed: 20

    Connections {
        target: Constants
        onAddLog: {
            Constants.logsList.append({log:newLog})
        }
        onClearLogs: {
            Constants.logsList.clear()
        }
    }

    Image {
        id: background
        width: parent.width
        height: parent.height
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Modale.svg")
        fillMode: Image.Stretch
        anchors.fill: parent
    }

    Image {
        id: returnButton
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FermerModale.svg")
        height: parent.height * 0.12
        width: parent.width * 0.075
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: (parent.width * 0.02) + (width * 0.5)
        MouseArea {
            anchors.fill: parent
            onClicked: coreEtatLogs.visible = !coreEtatLogs.visible
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
            Layout.preferredHeight: 20
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
                border.color: Constants.colorText
                radius: width * 0.05

                RowLayout {
                    anchors.centerIn: parent
                    width: parent.width - (parent.border.width * 3)
                    height: parent.height- (parent.border.width * 3)

                    Rectangle {
                        Layout.preferredWidth: 30
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        color: "transparent"
                        Image {
                            anchors.fill: parent
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaire.svg")
                            fillMode: Image.PreserveAspectFit
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 70
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        color: "transparent"
                        Label {
                            id: modalTitleText
                            anchors.centerIn: parent
                            width: parent.width
                            height: parent.height
                            text: "Journal de logs"
                            color: Constants.colorText
                            font.pixelSize: width * 0.12
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }

        Item {
            //Spacer
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        Rectangle {
            id: displayLogs
            Layout.preferredHeight: 80
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"

            ListView {
                clip: true
                id: logsListView
                anchors.fill: parent
                model: _logsList

                ScrollBar.vertical: ScrollBar
                {
                    policy: parent.contentHeight > parent.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                    width:parent.width*0.03
                    background: Rectangle {
                        implicitWidth: parent.parent.width*0.01
                        color: "#00000000"  // Couleur du fond de la scrollbar
                        radius: 6
                        border.color: Constants.colorText
                    }

                    contentItem: Rectangle {
                        implicitWidth: parent.parent.width*0.01
                        color: Constants.colorText  // Couleur de la barre de défilement
                        radius: 6
                    }
                }

                delegate : Item {
                    width: parent.width*0.95
                    height: parent.parent.height * (1.0/maxItemDisplayed)
                    //Layout.minimumHeight: 30

                    Label {
                        clip: true
                        height: parent.height
                        width: parent.width
                        anchors.left: parent.left
                        text: model.log
                        color: Constants.colorText
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        elide: Label.ElideRight
                    }
                }

            }
        }
    }

    // //Test ajout de log et clear
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         if(Constants.logsList.count >= 40)
    //             Constants.clearLogs()
    //         Constants.addLog("Hello world!")

    //     }
    // }

}
