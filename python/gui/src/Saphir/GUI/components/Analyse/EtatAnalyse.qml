import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Item {
    property bool modeSelected: Constants.isFileSelectionMode

    function selectMode(mode)
    {
        Constants.isFileSelectionMode = mode

        if(Constants.isFileSelectionMode) {
            ApplicationController.stop_analysis()
        } else {
            ApplicationController.start_analysis()
        }
    }

    Connections {
        target: ApplicationController

        onGlobalProgressChanged: {
            loadingCircleCanvas.requestPaint()
        }
    }

    ColumnLayout
    {
        anchors.fill: parent

        Image {
            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BarreSeparationAnalyse.svg")
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: 10
        }

        /*Rectangle {
            Layout.preferredHeight: 10
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            Image {
                anchors.fill: parent
                source: !modeSelected ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BoutonScanAutoActive.svg")
                                      : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BoutonScanAutoDesactive.svg")
                fillMode: Image.PreserveAspectFit
                MouseArea {
                    anchors.fill: parent
                    onClicked: { selectMode(false) }
                }
            }
        }


        Rectangle {
            Layout.preferredHeight: 10
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            Image {
                anchors.fill: parent
                source: modeSelected ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BoutonScanSelectActive.svg")
                                     : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BoutonScanSelectDesactive.svg")
                fillMode: Image.PreserveAspectFit

                //Layout.alignment: Qt.AlignCenter
                MouseArea {
                    anchors.fill: parent
                    onClicked: { selectMode(true) }
                }
            }
        }*/

        Rectangle {
            Layout.preferredHeight: 40
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            Rectangle
            {
                id: loadingCircle
                anchors {
                    centerIn: parent
                    margins: 5
                }
                height: Math.min(parent.height, parent.width)
                width: Math.min(parent.height, parent.width)
                color: "transparent"
                radius: width * 0.5
                border.color: Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "lightblue" : "#292929"
                border.width: parent.width * 0.01
                Canvas {
                    id: loadingCircleCanvas
                    anchors.fill: parent
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.beginPath()
                        ctx.strokeStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#00D400" : Constants.colorGreen
                        ctx.lineWidth = parent.parent.width * 0.06
                        ctx.arc(width * 0.5,
                                height * 0.5,
                                width * 0.45 - ctx.lineWidth * 0.5,
                                -Math.PI * 0.5,
                                -Math.PI * 0.5 + Math.PI * 2 * Constants.globalProgress)
                        ctx.stroke()
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: -7
                    Text {
                        text: Math.round(Constants.globalProgress * 100) + " %"
                        anchors.horizontalCenter: parent.horizontalCenter
                        font.pixelSize: Math.min(loadingCircle.height * 0.2, loadingCircle.width * 0.2)
                        font.bold: true
                        color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? Constants.colorText : "#7E8EAC"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter

                    }

                    Text {
                        //text: "Rest. " + Constants.globalTimeLeft + " sec"
                        text: "Rest. " + formatDuration(Constants.globalTimeLeft)
                        anchors.horizontalCenter: parent.horizontalCenter
                        font.pixelSize: Math.min(loadingCircle.height * 0.1, loadingCircle.width * 0.1)
                        color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? Constants.colorText : "#7E8EAC"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }                          

                Rectangle {
                    anchors {
                        fill: parent
                        margins: width*0.01
                    }
                    radius: width/2
                    opacity: 0.7
                    visible: ApplicationController.longProcessRunning

                    BusyIndicator {
                        id: busy

                        anchors {
                            fill: parent
                            margins: width*0.3
                        }

                    }
                }


            }
        }


        Rectangle {
            id: buttonsContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: 20
            color: "transparent"

            RowLayout {
                anchors.fill: parent
                
                Rectangle {
                    Layout.preferredWidth: 35
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignLeft
                    color: "transparent"

                    Image {
                        id: buttonPause
                        /*source: ApplicationController.analysisReady ?
                                    (Constants.isAnalysePlaying == false ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PauseActif.svg")
                                                                         : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PauseInactif.svg"))
                                    : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PauseInactif.svg")*/
                        source: ApplicationController.analysisReady && ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PauseActif.svg") : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PauseInactif.svg")
                        fillMode: Image.PreserveAspectFit
                        anchors.fill: parent

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if(ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted) {
                                    ApplicationController.stop_analysis()
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: Math.min(buttonPause.width, buttonPause.height)
                        height: width
                        color: "transparent"
                        radius: width/2
                        anchors.centerIn: buttonPause
                        visible: !Constants.isAnalysePlaying && ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted
                        border {
                            width: buttonPause.width/10
                            color: Constants.colorBlue
                        }
                    }
                }

                Item { //Spacer
                    Layout.preferredWidth: 30
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                }

                Rectangle {
                    Layout.preferredWidth: 35
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignRight
                    color: "transparent"

                    Image {
                        id: buttonPlay
                        /*source: ApplicationController.analysisReady ?
                                        (Constants.isAnalysePlaying ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PlayActif.svg")
                                            : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PlayInactif.svg"))
                                    : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PlayInactif.svg")*/
                        source: ApplicationController.analysisReady && ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PlayActif.svg") : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "PlayInactif.svg")
                        fillMode: Image.PreserveAspectFit
                        anchors.fill: parent
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if(ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted) {
                                    ApplicationController.start_analysis()
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: Math.min(buttonPlay.width, buttonPlay.height)
                        height: width
                        color: "transparent"
                        radius: width/2
                        anchors.centerIn: buttonPlay
                        visible: Constants.isAnalysePlaying && ApplicationController.systemState !== Enums.SystemState.AnalysisCompleted
                        border {
                            width: buttonPlay.width/10
                            color: Constants.colorBlue
                        }
                    }
                }
            }
        }

        Image {
            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BarreSeparationProgression.svg")
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredHeight: 10
        }
    }

    function formatDuration(seconds) {
        if (seconds < 60) {
            return seconds +" sec"  // Format ss
        } else if (seconds < 3600) {
            let minutes = Math.floor(seconds / 60)
            let remainingSeconds = seconds % 60
            return minutes + " mn " + remainingSeconds +" s"  // Format mm:ss
        } else {
            let hours = Math.floor(seconds / 3600)
            let remainingMinutes = Math.floor((seconds % 3600) / 60)
            return hours + " h " + remainingMinutes +" mn"  // Format hh:mm
        }
    }

    // Fonction pour ajouter un zéro devant les nombres inférieurs à 10
    function padWithZero(value) {
        return value < 10 ? "0" + value : value.toString()
    }

    // Timer {
    //     interval: 1000
    //     running: Constants.globalProgress <= 100
    //     repeat: true
    //     onTriggered: Constants.updateProgress(Constants.globalProgress + 0.01, Constants.globalTimeLeft-1)
    // }
}
