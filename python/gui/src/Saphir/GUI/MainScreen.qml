/*
This is a UI file (.ui.qml) that is intended to be edited in Qt Design Studio only.
It is supposed to be strictly declarative and only uses a subset of QML. If you edit
this file manually, you might introduce QML code that is not supported by Qt Design Studio.
Check out https://doc.qt.io/qtcreator/creator-quick-ui-forms.html for details on .ui.qml files.
*/

import QtQuick
import "components"
import "components/Analyse"
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import net.alefbet
import "imports"

Item {
    property double coreMargin : 0.03

    /*Connections {
        target: Constants
        onCopySaneFiles: {
            if(!Constants.isCopyingSaneFiles)
                Constants.isCopyingSaneFiles = true
        }
        onUpdateCopySaneFilesProgress: {
            Constants.copyProgress = newProgress
            if (newProgress >= 1.0)
                Constants.isCopyingSaneFiles = false
        }
    }*/

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath  + "FondEcran.svg")
        width: parent.width
        height: parent.height
        fillMode: Image.PreserveAspectCrop
        anchors.fill: parent
    }

    Item {
        id: patternOverlay
        width: parent.width
        height: parent.height
        anchors.centerIn: parent

        Image {
            id: pattern
            source: Qt.resolvedUrl(Constants.colorModePath  + "MotifHexagonal.svg")
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
            anchors.fill: parent            
        }

        Colorize {
            id: masqueCouleur
            anchors.fill: pattern
            source: pattern
            visible: ApplicationController.infectedFilesCount > 0

            hue: Constants.colorSystemUsed.hslHue
            saturation: Constants.colorSystemUsed.hslSaturation
            lightness: Constants.colorSystemUsed.hslLightness
            opacity: ApplicationController.systemUsed ? 0.5 : 1.0
        }
    }

    ColumnLayout
    {
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5
        anchors.topMargin: 5
        anchors.bottomMargin: 5
        Header // Header bleu en haut
        {
            id: header
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredHeight: 7
        }
        RowLayout // Partie mode + Luminosite
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredHeight: 7
            Layout.leftMargin: width * coreMargin
            Layout.rightMargin: width * coreMargin

            Mode
            {                
                Layout.preferredWidth: 20
                Layout.fillHeight: true
                Layout.fillWidth: true
            }

            Item {
                Layout.preferredWidth: 60
                Layout.fillHeight: true
                Layout.fillWidth: true
            }

            Luminosite
            {
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                Layout.preferredWidth: 20
                Layout.fillHeight: true
                Layout.fillWidth: true
            }
        }

        Core // coeur de l'application
        {
            id: appCore
            Layout.leftMargin: width * coreMargin
            Layout.rightMargin: width * coreMargin
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredHeight: 90

            Image {
                id: activeSystemButton
                source: systemState.visible ? Qt.resolvedUrl(Constants.colorModePath  + "EtatSystemeActive.svg")
                                            : Qt.resolvedUrl(Constants.colorModePath  + "EtatSystemeActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.295)
                width: parent.width * 0.06
                height: parent.height * 0.1

                MouseArea {
                    anchors.fill: parent
                    onClicked: systemState.visible = !systemState.visible
                }

                HelpTip {
                    libelle: "Afficher l'état du système"
                }
            }

            Image {
                id: activeJournalButton
                source: logsState.visible ? Qt.resolvedUrl(Constants.colorModePath  + "JournalActive.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath  + "JournalActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.471)
                width: parent.width * 0.06
                height: parent.height * 0.1

                MouseArea {
                    anchors.fill: parent
                    onClicked: logsState.visible = !logsState.visible
                }

                HelpTip {
                    libelle: "Afficher le journal du système"
                }
            }

            Image {

                property bool isRestartButtonActive: false

                id: restartButton
                source: isRestartButtonActive ? Qt.resolvedUrl(Constants.colorModePath  + "RedemarrerActive.svg")
                                              : Qt.resolvedUrl(Constants.colorModePath  + "RedemarrerActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.648)
                width: parent.width * 0.05
                height: parent.height * 0.08

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        confirmRestartButton.visible = !confirmRestartButton.visible
                        confirmExitButton.visible = false
                        exitButton.isExitButtonActive = false
                        restartButton.isRestartButtonActive = !parent.isRestartButtonActive
                    }
                }

                Image {
                    id: confirmRestartButton
                    visible: false
                    source: Qt.resolvedUrl(Constants.colorModePath  + "ConfirmerRedemarrer.svg")
                    fillMode: Image.PreserveAspectFit
                    horizontalAlignment: Image.AlignLeft
                    anchors.left: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: parent.height

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {  
                            restartButton.visible = false                           
                            ApplicationController.reset() 
                        }
                    }
                }

                DropShadow {
                    anchors.fill: confirmRestartButton
                    source: confirmRestartButton
                    radius: 20
                    color: "#333"
                    visible: confirmRestartButton.visible
                }

                HelpTip {
                    libelle: "Réinitialiser le système"
                }
            }

            Image {

                property bool isExitButtonActive: false

                id: exitButton
                source: isExitButtonActive ? Qt.resolvedUrl(Constants.colorModePath  + "QuitterActive.svg")
                                           : Qt.resolvedUrl(Constants.colorModePath  + "QuitterActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.755)
                width: parent.width * 0.05
                height: parent.height * 0.08

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        confirmRestartButton.visible = false
                        restartButton.isRestartButtonActive = false
                        confirmExitButton.visible = !confirmExitButton.visible
                        exitButton.isExitButtonActive = !exitButton.isExitButtonActive
                    }
                }

                Image {
                    id: confirmExitButton
                    source: Qt.resolvedUrl(Constants.colorModePath  + "ConfirmerQuitter.svg")
                    visible: false
                    fillMode: Image.PreserveAspectFit
                    horizontalAlignment: Image.AlignLeft
                    anchors.left: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: parent.height

                    MouseArea {
                        anchors.fill: parent
                        onClicked: { 
                            exitButton.visible = false
                            ApplicationController.shutdown() 
                        }
                    }
                }

                DropShadow {
                    anchors.fill: confirmExitButton
                    source: confirmExitButton
                    radius: 20
                    color: "#333"
                    visible: confirmExitButton.visible
                }

                HelpTip {
                    libelle: "Eteindre le système"
                }
            }            

            Item {
                width: parent.width * 0.075
                height: parent.height * 0.1
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: (width * 0.5) - parent.width * 0.01
                anchors.bottomMargin: (height * 0.5) - parent.height * 0.01                

                Image {
                    id: bigFileListButton
                    source: bigFileList.visible ? Qt.resolvedUrl(Constants.colorModePath  + "EtirerConteneurGaucheActive.svg")
                                                : Qt.resolvedUrl(Constants.colorModePath  + "EtirerConteneurGaucheActif.svg")
                    fillMode: Image.PreserveAspectFit
                    anchors.fill: parent

                    MouseArea {
                        anchors.fill: parent
                        onClicked: bigFileList.visible = !bigFileList.visible
                    }
                }

                HelpTip {
                    libelle: "Afficher le navigateur en grand"
                    y: parent.height/2
                    visible: Constants.afficherAide && ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection
                }
            }

            RowLayout {
                id: copySaneFilesComponent
                visible: Constants.isOutputUSBPlugged && ApplicationController.systemState === Enums.SystemState.AnalysisCompleted
                width: parent.width * 0.2
                height: parent.height * 0.1
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: parent.width * 0.12 + (width * 0.5)
                anchors.topMargin: parent.height * 0.2 + (height * 0.5)
                spacing: 10

                Item {
                    Layout.preferredWidth: 40
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Image {
                        id: copySaneFilesButton
                        anchors.fill: parent
                        Layout.alignment: Qt.AlignTop
                        source: Constants.isCopyingSaneFiles ? Qt.resolvedUrl(Constants.colorModePath  + "CopierFichiersActive.svg")
                                                                 : Qt.resolvedUrl(Constants.colorModePath  + "CopierFichiersActif.svg")
                        fillMode: Image.PreserveAspectFit

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                ApplicationController.start_transfer()
                            }
                        }
                    }
                }

                Item {
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Label {
                        anchors.fill: parent
                        color: Constants.colorText
                        text: "Copier les fichiers sains"
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                ApplicationController.start_transfer()
                            }
                        }
                    }
                }                
            }

            Rectangle {
                id: copyProgressBar
                visible: Constants.isCopyingSaneFiles
                width: parent.width * 0.2
                height: parent.height * 0.05
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: (width * 0.5) - (parent.width * 0.05)
                anchors.topMargin: parent.height * 0.1 + (height * 0.5)
                color: "transparent"
                border.width: height * 0.1
                border.color: Constants.colorText
                
                Rectangle {
                    width: Math.min(parent.width * ApplicationController.transferProgress, parent.width)
                    height: parent.height
                    color: Constants.colorBlue
                    opacity: 0.3
                }
                Label {
                    anchors.centerIn: parent
                    width: parent.width
                    height: parent.height
                    text: Math.round(ApplicationController.transferProgress * 100.0) + "%"
                    color: Constants.colorText
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Image {
        id: helpButton
        source: helper.visible  ? Qt.resolvedUrl(Constants.colorModePath  + "AideActive.svg")
                                : Qt.resolvedUrl(Constants.colorModePath  + "AideActif.svg")
        fillMode: Image.PreserveAspectFit
        anchors {
            right: parent.right
            rightMargin: 0
            bottom: parent.bottom
            bottomMargin: (parent.height * 0.145)
        }

        width: parent.width * 0.05
        height: parent.height * 0.08

        MouseArea {
            anchors.fill: parent
            onClicked: {
                Constants.afficherAide = !Constants.afficherAide
            }
        }
    }

    //Modales
    Item {
        //Modals holder
        anchors.fill: parent
        EtatSysteme {
            id: systemState
            visible: false
            anchors.centerIn: parent
            width: parent.width * 0.9
            height: parent.height * 0.9
        }

        EtatLogs {
            id: logsState
            visible: false            
            anchors.centerIn: parent
            width: parent.width * 0.9
            height: parent.height * 0.9
        }

        GrandeListeDossier {
            id: bigFileList
            visible: false
            anchors.centerIn: parent
            width: parent.width * 0.9
            height: parent.height * 0.9
        }
    }

    Item {
        id: helper
        visible: Constants.afficherAide
        anchors.fill: parent

        Rectangle {
            id: helperBackground
            anchors.fill: parent
            color: Constants.colorText
            opacity: 0.2
        }
    }

    PopupAnalyseIntegrale {
        id: popupAnalyseIntegrale
        anchors.centerIn: parent  
        visible: false

        onAccepted: {
            visible = false
            ApplicationController.start_full_analysis()            
        }

        onRejected: {
            visible = false
            ApplicationController.analysisMode = Enums.AnalysisMode.AnalyseSelection
            ApplicationController.update_source_files_list()
        }
    }

    PopupMustReset {
        id: popupMustReset 
        anchors.centerIn: parent
        visible: false

        onAccepted: {
            visible = false      
        }
    }

    PopupAnalysisFinished {
        id: popupAnalysisFinished
        anchors.centerIn: parent
        visible: false

        onAccepted: {
            visible = false
        }
    }

    PopupReinitialisation {
        id: popupReinitialisation
        anchors.centerIn: parent
        visible: false
    }

    PopupShuttingDown {
        id: popupShuttingDown
        anchors.centerIn: parent 
    }

    Connections {
        target: ApplicationController
        
        function onSourceReadyChanged() {
            popupAnalyseIntegrale.visible = ApplicationController.sourceReady
        }

        function onSystemMustBeReset() {
            popupMustReset.visible = true
        }        

        function onSystemStateChanged() {
            if(ApplicationController.systemState === Enums.SystemState.AnalysisCompleted) {
                popupAnalysisFinished.visible = true
            } else if(ApplicationController.systemState === Enums.SystemState.SystemResetting) {
                popupAnalysisFinished.visible = false
                popupReinitialisation.visible = true
                popupMustReset.visible = false
            } else if(ApplicationController.systemState === Enums.SystemState.SystemShuttingDown) {
                popupAnalysisFinished.visible = false
                popupReinitialisation.visible = false
                popupMustReset.visible = false
                popupShuttingDown.visible = true
            }
        }

        function onAnalysisReadyChanged() {
            if(popupReinitialisation.visible && ApplicationController.analysisReady) {
                popupReinitialisation.visible = false
            }
        }
    }

    Component.onCompleted: {
        if(ApplicationController.sourceReady && ApplicationController.analysisMode === Enums.AnalysisMode.Undefined) {
            popupAnalyseIntegrale.visible = true
        }

        if(ApplicationController.systemState === Enums.SystemState.onSystemMustBeReset) {
            popupMustReset.visible = true
        }

        if(ApplicationController.systemState === Enums.SystemState.AnalysisCompleted) {
            popupAnalysisFinished.visible = true
        }
    }

}
