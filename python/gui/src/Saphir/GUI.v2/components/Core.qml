import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

import "EntreeSortie"
import "Analyse"
import "../imports"

Item {
    id: rootCore    

    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(Constants.colorModePath  + "LigneContour.svg")
        //fillMode: Image.PreserveAspectCrop
    }

    Item {
        id: coreContainer
        anchors.centerIn: parent
        anchors.verticalCenterOffset: parent.width * 0.03
        height: parent.height * 0.85
        width: parent.width * 0.9
    }

    ColumnLayout {
        anchors.fill: coreContainer

        GridLayout {
            id: coreGrid
            Layout.preferredHeight: 95
            Layout.fillHeight: true
            Layout.fillWidth: true

            columns: 3
            rows: 2

            //ROW 1
            Item {
                Layout.column: 0
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                visible: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection

                Entree {
                    id: entreeUSB
                    anchors.centerIn: parent
                    height: parent.height
                    width: parent.width * 0.9
                }

                /*Connections {
                    target: entreeUSB
                    onSelectedSignal: if (entreeUSB.selected) sortieUSB.selected=false;
                }*/
            }

            Item {
                Layout.column: 1
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25

                EtatFichier {
                    id: filesState
                    anchors.fill: parent
                }

            }
            Item {
                Layout.column: 2
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25

                RowLayout {
                    anchors.fill: parent

                    Entree {
                        id: entreeUSB2
                        Layout.alignment: Qt.AlignLeft
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: visible ? parent.width/2 - img.width : 0
                        visible: ApplicationController.analysisMode !== Enums.AnalysisMode.AnalyseSelection
                    }

                    Item {
                        id: img
                        Layout.alignment: Qt.AlignRight
                        Layout.preferredHeight: parent.height/2.5
                        Layout.preferredWidth: parent.height/2.5
                        visible: Constants.isOutputUSBPlugged && ApplicationController.systemState === Enums.SystemState.AnalysisCompleted

                        Image {
                            id: copySaneFilesButton
                            anchors {
                                top: parent.top
                                bottom: parent.bottom
                                right: parent.right
                            }

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

                        HelpTip {
                            libelle: "Copier les fichiers sains"
                            y: parent.height/-2
                            visible: Constants.afficherAide & parent.visible
                        }
                    }

                    Sortie {
                        id: sortieUSB
                        //Layout.alignment: Qt.AlignRight
                        //Layout.preferredHeight: parent.height
                        Layout.preferredHeight: parent.height
                        //Layout.preferredWidth: parent.width/2 - img.width
                        Layout.fillWidth: true
                        //Layout.leftMargin: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection ? parent.width*0.3 : 0
                    }
                }

            }

            //ROW 2
            Item {
                Layout.column: 0
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 35
                visible: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection

                ListeDossier
                {
                    id: fileSelection
                    anchors.fill: parent

                    HelpTip {
                        anchors.centerIn: parent
                        libelle: "Sélection des fichiers"
                    }
                }

            }
            Item {
                Layout.column: 1
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 15

                EtatAnalyse {
                    id: etatAnalyse
                    anchors.fill: parent
                }
            }
            Item {
                Layout.column: 2
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 45

                ListeFichier {
                    anchors.fill: parent
                    //_fileList: Constants.runningFileList

                    HelpTip {
                        anchors.centerIn: parent
                        libelle: "Etat et progression des fichiers"
                    }
                }
            }
        }

        Item {
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            Layout.fillWidth: true

            Legende {
                anchors.centerIn: parent
                height: parent.height
            }
        }
    }
}
