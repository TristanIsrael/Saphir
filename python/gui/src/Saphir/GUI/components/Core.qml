import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

import "EntreeSortie"
import "Analyse"
import "../imports"

Rectangle {
    id: rootCore
    color: "transparent"


    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LigneContour.svg")
        //fillMode: Image.PreserveAspectCrop
    }

    Rectangle {
        id: coreContainer
        anchors.centerIn: parent
        anchors.verticalCenterOffset: parent.width * 0.03
        height: parent.height * 0.85
        width: parent.width * 0.9
        color: "transparent"

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
            Rectangle {
                Layout.column: 0
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                color: "transparent"
                visible: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection

                Entree {
                    id: entreeUSB
                    anchors.centerIn: parent
                    height: parent.height
                    width: parent.width * 0.9
                }

                Connections {
                    target: entreeUSB
                    onSelectedSignal: if (entreeUSB.selected) sortieUSB.selected=false;
                }
            }

            Rectangle {
                Layout.column: 1
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                color: "transparent"

                EtatFichier {
                    id: filesState
                    anchors.fill: parent
                }

            }
            Rectangle {
                Layout.column: 2
                Layout.row: 0
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 25
                color: "transparent"

                RowLayout {
                    anchors.fill: parent

                    Entree {
                        id: entreeUSB2
                        Layout.alignment: Qt.AlignLeft
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: parent.width/2
                        visible: ApplicationController.analysisMode !== Enums.AnalysisMode.AnalyseSelection
                    }

                    Connections {
                        target: entreeUSB2
                        onSelectedSignal: if (entreeUSB2.selected) sortieUSB.selected=false;
                    }

                    Sortie {
                        id: sortieUSB
                        Layout.alignment: Qt.AlignRight
                        Layout.preferredHeight: parent.height
                        Layout.fillWidth: true
                        Layout.leftMargin: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection ? parent.width*0.3 : 0
                        //Layout.preferredWidth: parent.width/2

                    }
                }
                // Connections {
                //     target: sortieUSB
                //     onSelectedSignal: if (sortieUSB.selected) entreeUSB.selected=false;
                // }

            }

            //ROW 2
            Rectangle {
                Layout.column: 0
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 35
                color: "transparent"
                visible: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection

                ListeDossier
                {
                    id: fileSelection
                    anchors.fill: parent
                }

            }
            Rectangle {
                Layout.column: 1
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 15
                color: "transparent"

                EtatAnalyse {
                    id: etatAnalyse
                    anchors.fill: parent
                }
            }
            Rectangle {
                Layout.column: 2
                Layout.row: 1
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredHeight: 75
                Layout.preferredWidth: 45
                color: "transparent"

                ListeFichier {
                    anchors.fill: parent
                    //_fileList: Constants.runningFileList
                }
            }
        }

        Rectangle {
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            Legende {
                anchors.centerIn: parent
                height: parent.height
            }
        }
    }
}
