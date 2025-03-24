import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
                Sortie {
                    id: sortieUSB
                    anchors.right: parent.right
                    height: parent.height
                    width: parent.width * 0.7
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
                ListeDossier
                {
                    id: fileSelection
                    anchors.fill: parent
                    _fileList: Constants.fileList
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
                    _fileList: Constants.runningFileList
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
