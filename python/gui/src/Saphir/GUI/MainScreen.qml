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

Rectangle {
    property double coreMargin : 0.03
    color: "transparent"

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

    Rectangle {
        id: patternOverlay
        width: parent.width
        height: parent.height
        color: "transparent"
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
                Layout.preferredWidth: 65
                Layout.fillHeight: true
                Layout.fillWidth: true
            }

            Luminosite
            {
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                Layout.preferredWidth: 15
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
            }            

            Rectangle {
                width: parent.width * 0.075
                height: parent.height * 0.1
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: (width * 0.5) - parent.width * 0.01
                anchors.bottomMargin: (height * 0.5) - parent.height * 0.01
                color: "transparent"

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

                Rectangle {
                    Layout.preferredWidth: 40
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"

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

                Rectangle {
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"

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

        //anchors.horizontalCenter: parent.right
        //anchors.verticalCenter: parent.top
        //anchors.verticalCenterOffset: (parent.height * 0.855)
        //anchors.horizontalCenterOffset: parent.width * 0.02
        width: parent.width * 0.05
        height: parent.height * 0.08

        MouseArea {
            anchors.fill: parent
            onClicked: {
                helper.visible = !helper.visible
            }
        }
    }

    //Modales
    Rectangle {
        //Modals holder
        anchors.fill: parent
        color: "transparent"
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

    Rectangle {
        id: helper
        visible: false
        width: parent.width
        height: parent.height
        color: "transparent"
        anchors.centerIn: parent

        Rectangle {
            id: helperBackground
            anchors.fill: parent
            color: Constants.colorText
            opacity: 0.5
        }

        Rectangle {
            width: parent.width * 0.2
            height: parent.height * 0.05
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: parent.height * 0.05
            anchors.horizontalCenterOffset: -parent.width * 0.12
            color: "transparent"
            Image {
                anchors.fill: parent
                source: Qt.resolvedUrl(Constants.colorModePath  + "ContainerSupportSortie.svg")
                fillMode: Image.Stretch
            }
            Label {
                anchors.fill: parent
                text: "Classification"
                color: Constants.colorText
                font.pixelSize: Math.min(height * 0.6, width * 0.15)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                layer.enabled: true
            }
        }

        Rectangle {
            width: parent.width * 0.2
            height: parent.height * 0.05
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: -parent.width * 0.25
            anchors.verticalCenterOffset: parent.height * 0.1
            color: "transparent"
            Image {
                anchors.fill: parent
                source: Qt.resolvedUrl(Constants.colorModePath  + "ContainerSupportSortie.svg")
                fillMode: Image.Stretch
            }
            Label {
                anchors.fill: parent
                text: "Contenu support d'entrée"
                color: Constants.colorText
                font.pixelSize: Math.min(height * 0.6, width * 0.15)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                layer.enabled: true
            }
        }

        Rectangle {
            width: parent.width * 0.2
            height: parent.height * 0.05
            anchors.centerIn: parent
            anchors.horizontalCenterOffset: parent.width * 0.225
            anchors.verticalCenterOffset: parent.height * 0.1
            color: "transparent"
            Image {
                anchors.fill: parent
                source: Qt.resolvedUrl(Constants.colorModePath  + "ContainerSupportSortie.svg")
                fillMode: Image.Stretch
            }
            Label {
                anchors.fill: parent
                text: "Avancement analyse"
                color: Constants.colorText
                font.pixelSize: Math.min(height * 0.6, width * 0.15)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                layer.enabled: true
            }
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

    Connections {
        target: ApplicationController
        
        onSourceReadyChanged: function() {
            popupAnalyseIntegrale.visible = ApplicationController.sourceReady
        }

        onSystemMustBeReset: function() {
            popupMustReset.visible = true
        }        

        onSystemStateChanged: function() {
            if(ApplicationController.systemState === Enums.SystemState.AnalysisCompleted) {
                popupAnalysisFinished.visible = true
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
