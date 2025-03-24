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
import "imports"

Rectangle {
    property double coreMargin : 0.03
    color: "transparent"

    Connections {
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
    }

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FondEcran.svg")
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
            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "MotifHexagonal.svg")
            width: parent.width
            height: parent.height
            fillMode: Image.PreserveAspectCrop
            anchors.fill: parent
        }
    }

    ColumnLayout
    {
        anchors.fill: parent
        anchors.leftMargin: 26
        anchors.rightMargin: 26
        anchors.topMargin: 18
        anchors.bottomMargin: 26
        Header // Header bleu en haut
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredHeight: 5
        }
        RowLayout // Partie mode + Luminosite
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredHeight: 5
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
                source: systemState.visible ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "EtatSystemeActive.svg")
                                            : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "EtatSystemeActif.svg")
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
                source: logsState.visible ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "JournalActive.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "JournalActif.svg")
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
                source: isRestartButtonActive ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "RedemarrerActive.svg")
                                              : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "RedemarrerActif.svg")
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
                        parent.isRestartButtonActive = !parent.isRestartButtonActive
                    }
                }

                Image {
                    id: confirmRestartButton
                    visible: false
                    source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ConfirmerRedemarrer.svg")
                    fillMode: Image.PreserveAspectFit
                    horizontalAlignment: Image.AlignLeft
                    anchors.left: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: parent.height

                    MouseArea {
                        anchors.fill: parent
                        onClicked: { Constants.restart() }
                    }
                }
            }

            Image {

                property bool isExitButtonActive: false

                id: exitButton
                source: isExitButtonActive ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "QuitterActive.svg")
                                           : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "QuitterActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.755)
                width: parent.width * 0.05
                height: parent.height * 0.08

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        confirmExitButton.visible = !confirmExitButton.visible
                        exitButton.isExitButtonActive = !exitButton.isExitButtonActive
                    }
                }

                Image {
                    id: confirmExitButton
                    source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ConfirmerQuitter.svg")
                    visible: false
                    fillMode: Image.PreserveAspectFit
                    horizontalAlignment: Image.AlignLeft
                    anchors.left: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: parent.height

                    MouseArea {
                        anchors.fill: parent
                        onClicked: { Constants.quit() }
                    }
                }
            }

            Image {
                id: helpButton
                source: helper.visible  ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "AideActive.svg")
                                        : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "AideActif.svg")
                fillMode: Image.PreserveAspectFit
                anchors.horizontalCenter: parent.right
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: (parent.height * 0.855)
                anchors.horizontalCenterOffset: parent.width * 0.02
                width: parent.width * 0.05
                height: parent.height * 0.08

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        helper.visible = !helper.visible
                    }
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
                    source: bigFileList.visible ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "EtirerConteneurGaucheActive.svg")
                                                : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "EtirerConteneurGaucheActif.svg")
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
                visible: Constants.isOutputUSBPlugged
                width: parent.width * 0.2
                height: parent.height * 0.05
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.rightMargin: parent.width * 0.12 + (width * 0.5)
                anchors.topMargin: parent.height * 0.26 + (height * 0.5)
                Rectangle {
                    Layout.preferredWidth: 20
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                    Image {
                        id: copySaneFilesButton
                        anchors.fill: parent
                        source: Constants.isCopyingSaneFiles ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CopierFichiersActive.svg")
                                                                 : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CopierFichiersActif.svg")
                        fillMode: Image.PreserveAspectFit
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                Constants.copySaneFiles()
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
                    width: Math.min(parent.width * Constants.copyProgress, parent.width)
                    height: parent.height
                    color: Constants.colorText
                    opacity: 0.3
                }
                Label {
                    anchors.centerIn: parent
                    width: parent.width
                    height: parent.height
                    text: Math.round(Constants.copyProgress * 100.0) + "%"
                    color: Constants.colorText
                    font.pixelSize: Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
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
            _antivirusList: Constants.antivirusList
            _diskState: Constants.diskState
            anchors.centerIn: parent
            width: parent.width * 0.9
            height: parent.height * 0.9
        }

        EtatLogs {
            id: logsState
            visible: false
            _logsList: Constants.logsList
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
                source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportSortie.svg")
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
                source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportSortie.svg")
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
                source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportSortie.svg")
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

    //Test de la progression de la barre de chargement de copie des fichiers sains
    // Timer {
    //     interval: 500
    //     running: Constants.isCopyingSaneFiles
    //     repeat: true

    //     onTriggered: {
    //         if(Constants.copyProgress >= 1.0)
    //             Constants.copyProgress = 0.0
    //         Constants.updateCopySaneFilesProgress(Constants.copyProgress += 0.01)
    //     }
    // }


}
