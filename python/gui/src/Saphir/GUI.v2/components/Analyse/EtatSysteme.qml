import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import net.alefbet
import "../../imports"


Item {
    id: coreEtatSysteme    

    function getStateText(state)
    {
        if(state === "starting") {
            return "Démarrage"
        } else if(state === "unknown") {
            return "Inconnu";
        } else if(state === "error") {
            return "Erreur";
        } else if(state === "ready") {
            return "Prêt";
        }

        return "Inconnu"
    }

    function getStateColor(state) {
        //RGB
        if(state === "starting") {
            return Constants.colorBlue
        } else if(state === "error") {
            return Constants.colorRed
        } else if(state === "ready") {
            return Constants.colorGreen
        }

        return Constants.colorText
    }

    function getTypeIcone(type) {
        if(type === "antivirus") {
            return "ModaleEtatSystemeIconeAntivirus.svg"
        } else {
            return "ModaleEtatSystemeIconeAccesDisque.svg"
        }
    }

    Item {
        anchors.fill: parent

        Image {
            id: background
            source: Qt.resolvedUrl(Constants.colorModePath  + "Modale.svg")
            fillMode: Image.Stretch
            anchors.fill: parent
        }

        DropShadow {
            anchors.fill: background
            source: background
            radius: 20
            color: "#333"
            cached: true
        }
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
            onClicked: coreEtatSysteme.visible = !coreEtatSysteme.visible
        }
    }

    Item {
        id: modalContentContainer
        anchors.centerIn: parent
        width: parent.width * 0.96
        height: parent.height * 0.85
        anchors.verticalCenterOffset: parent.height * -0.05        
    }

    ColumnLayout {
        anchors.fill: modalContentContainer

        Rectangle {
            id: modalTitleHolder
            Layout.preferredHeight: parent.height/7
            Layout.fillWidth: true
            Layout.margins: height/10
            color: "transparent"
            
            border {
                width: width * 0.005
                color: Constants.colorText
            }
            radius: height/5

            RowLayout {
                anchors.centerIn: parent
                width: parent.width - (parent.border.width * 3)
                height: parent.height- (parent.border.width * 3)

                Item {
                    Layout.fillWidth: true
                }

                Image {
                    Layout.fillHeight: true
                    Layout.margins: height/10
                    source: Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaire.svg")
                    fillMode: Image.PreserveAspectFit
                }

                Item {
                    Layout.preferredWidth: parent.height/2
                }

                Label {
                    id: modalTitleText
                    //width: parent.width
                    Layout.preferredHeight: parent.height
                    text: "Etat du système"
                    color: Constants.colorText
                    font.pixelSize: height*0.7
                    //horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                Item {
                    Layout.fillWidth: true
                }
            }
        }

        TableView {
            id: componentsListView

            clip: true
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.margins: 40
            columnSpacing: 40
            rowSpacing: 20

            model: ApplicationController.componentsModel

            ScrollBar.vertical: ScrollBar
            {
                policy: parent.contentHeight > parent.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                width: parent.width*0.03
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
                implicitHeight: 40
                implicitWidth: column === 0 ? icn.width : lbl.width

                Image {
                    id: icn
                    source: Qt.resolvedUrl(Constants.colorModePath  + coreEtatSysteme.getTypeIcone(display))
                    height: parent.height*0.8
                    fillMode: Image.PreserveAspectFit
                    visible: column === 0
                    anchors.centerIn: parent
                }

                Label {            
                    id: lbl    
                    clip: true
                    text: column === 2 ? getStateText(display) : column > 0 ? display : ""
                    color: column === 2 ? getStateColor(display) : column > 0 ? Constants.colorText : ""
                    font.pixelSize: parent.height
                    elide: Label.ElideRight
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 20

            Item {
                Layout.fillWidth: true
            }

            Label {
                id: lblAppInfo
                color: Constants.colorText
                font.pixelSize: 24
                text: "Saphir version " +Application.version
            }

            Label {
                id: lblSystemInfo
                color: Constants.colorText
                font.pixelSize: 24
                text: "PSEC version " +(ApplicationController.systemInformation["core"] !== undefined ? ApplicationController.systemInformation["core"]["version"] : "non identifiée")
                        +(ApplicationController.systemInformation["core"]["debug_on"] ? " débogage actif" : "")
            }

            Item {
                Layout.fillWidth: true
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

