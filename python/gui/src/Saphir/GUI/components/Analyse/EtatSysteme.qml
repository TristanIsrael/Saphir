import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"


Rectangle {
    id: coreEtatSysteme
    color: "transparent"
    property ListModel _antivirusList
    property int maxItemDisplayed: 4
    property int _diskState

    Connections {
        target: Constants
        onAddAntivirus: {
            for (let i = 0; i < Constants.antivirusList.count; i++)
            {
                if (Constants.antivirusList.get(i).backId === newId)
                    return
            }
            Constants.antivirusList.append({backId: newId, name: newName, state: newState})
        }
        onUpdateAntivirusSate: {
            for (let i = 0; i < Constants.antivirusList.count; i++) {
                if (Constants.antivirusList.get(i).backId === aBackId)
                {
                    Constants.antivirusList.get(i).state = newState
                }
            }
        }
        onClearAntivirusList: {
            Constants.antivirusList.clear()
        }
        onUpdateDiskState: {
            Constants.diskState = newState
        }
    }

    function getStateText(state)
    {
        switch(state)
        {
        case 0:
            return "Démarrage";
        case 1:
            return "Normal";
        case 2:
            return "Erreur";
        default:
            return "Inconnu";
        }
    }

    function getStateColor(state) {
        //RGB
        switch(state)
        {
        case 0:
            return Constants.colorBlue;
        case 1:
            return Constants.colorGreen;
        case 2:
            return Constants.colorRed;
        default:
            return Constants.colorText;
        }
    }

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Modale.svg")
        width: parent.width
        height: parent.height
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
            onClicked: coreEtatSysteme.visible = !coreEtatSysteme.visible
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
                border.color: Constants.colorText
                radius: width * 0.05
                Label {
                    id: modalTitleText
                    anchors.centerIn: parent
                    width: parent.width - (parent.border.width * 3)
                    height: parent.height - (parent.border.width * 3)
                    text: "Etat du système"
                    color: Constants.colorText
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

        Rectangle {
            Layout.preferredHeight: 50
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            ListView {
                clip: true
                id: antivirusListView
                Layout.alignment: Qt.AlignCenter
                width: parent.width
                height: parent.height
                model: _antivirusList

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

                delegate : Row {
                    width: parent.width*0.95
                    height: parent.parent.height * (1.0/maxItemDisplayed)
                    spacing: 0

                    Item {
                        height: parent.height
                        width: parent.width * 0.1
                        Image {
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModaleEtatSystemeIconeAntivirus.svg")
                            width:parent.width
                            height:parent.height
                            fillMode: Image.PreserveAspectFit
                            anchors.right: parent.right
                        }
                    }
                    Label {
                        // Layout.preferredWidth: 45
                        // Layout.fillHeight: true
                        // Layout.fillWidth: true
                        height: parent.height
                        width: parent.width * 0.2

                        text: model.name + " : "
                        color: Constants.colorText
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        horizontalAlignment: Text.AlignRight
                        verticalAlignment: Text.AlignVCenter
                    }
                    Label {
                        // Layout.preferredWidth: 35
                        // Layout.fillHeight: true
                        // Layout.fillWidth: true
                        height: parent.height
                        width: parent.width * 0.2

                        text: getStateText(model.state)
                        color: getStateColor(model.state)
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
        Rectangle {
            Layout.preferredHeight: 20
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            Row {
                anchors.fill: parent

                Item {
                    // Layout.preferredWidth: 10
                    // Layout.fillHeight: true
                    // Layout.fillWidth: true
                    height: parent.height
                    width: parent.width * 0.1
                    Image {
                        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModaleEtatSystemeIconeAccesDisque.svg")
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectFit
                    }

                }
                Label {
                    // Layout.preferredWidth: 40
                    // Layout.fillHeight: true
                    // Layout.fillWidth: true
                    height: parent.height
                    width: parent.width * 0.2

                    text: "Accès disque :"
                    color: Constants.colorText
                    font.pixelSize:  Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
                }
                Label {
                    // Layout.preferredWidth: 40
                    // Layout.fillHeight: true
                    // Layout.fillWidth: true
                    height: parent.height
                    width: parent.width * 0.2

                    text: getStateText(_diskState)
                    color: getStateColor(_diskState)
                    font.pixelSize:  Math.min(height * 0.6, width * 0.15)
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    // //Test ajout de antivirus et clear
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         if(Constants.antivirusList.count >= 10)
    //             Constants.clearAntivirusList()
    //         Constants.addAntivirus(Constants.antivirusList.count, "Hello world", Constants.AntivirusState.STARTING)
    //     }
    // }

    // //Test modification état antivirus
    // property int test_currentState: 0
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         test_currentState = (test_currentState + 1) % 3
    //         Constants.updateAntivirusSate(0, test_currentState)
    //     }
    // }

    //Test modification état antivirus
    // property int test_currentState: 0
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         test_currentState = (test_currentState + 1) % 3
    //         Constants.updateDiskState(test_currentState)
    //     }
    // }
}

