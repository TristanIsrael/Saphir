import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import QtQuick.Layouts
import net.alefbet
import "../../imports"
import "../../components"

Item {
    id: etatFichier    

    property int fichierNonAnalyse: fichierTotal - fichierSain - fichierInfecte - fichierAnalyse
    property int fichierAnalyse: 0
    property int fichierSain: ApplicationController.cleanFilesCount
    property int fichierInfecte: ApplicationController.infectedFilesCount
    property int fichierTotal: ApplicationController.queueSize

    Connections {
        target: ApplicationController

        function onQueueSizeChanged() { updateStateTracker() }
        function onInfectedFilesCountChanged() { updateStateTracker() }
        function onCleanFilesCountChanged() { updateStateTracker() }
        
    }

    function updateStateTracker() {
            /*Constants.countNotAnalysedFiles = ApplicationController.queueSize
            Constants.countAnalysingFiles = 1 //TODO
            Constants.countSaneFiles = ApplicationController.cleanFilesCount
            Constants.countInfectedFiles = ApplicationController.infectedFilesCount*/
            circleAnalyse.requestPaint()
            circleSane.requestPaint()
            circleInfected.requestPaint()
            circleNotAnalysed.requestPaint()
        }

    Item {
        id: roue
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height)
        height: Math.min(parent.width, parent.height)

        //Cercle fichiers analyse
        Rectangle {
            id: fileAnalyse
            anchors.centerIn: parent
            height: parent.height
            width: height
            color: "transparent"
            radius: width * 0.5
            border.color: Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#1677E6" : "#292929"
            border.width: parent.width * 0.01

            Canvas {
                id: circleAnalyse
                anchors.fill: parent
                onPaint: {
                    var startAngle = -Math.PI * 0.5
                    var endAngle = -Math.PI * 0.5 + Math.PI * 2 * (fichierAnalyse / fichierTotal)
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.beginPath()
                    ctx.strokeStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? Constants.currentColorMode === Constants.ColorMode.DARK ? "#A1C9F2" : "#1677E6" : Constants.colorBlue
                    ctx.globalAlpha = 0.3
                    ctx.lineWidth = parent.width * 0.15
                    ctx.arc(width * 0.5,
                            height * 0.5,
                            width * 0.47 - ctx.lineWidth * 0.5,
                            startAngle,
                            endAngle)
                    ctx.stroke()

                    //Affichage du texte
                    ctx.globalAlpha = 1.0 //Reset de l'alpha avant affichage du texte
                    var textPixelSize = Math.min(parent.height * 0.1, parent.width * 0.1)
                    var middleAngle = (startAngle + endAngle) * 0.5
                    var textRadius = (width * 0.22) + (ctx.lineWidth * 0.70) + (textPixelSize * 0.5)
                    var textX = width * 0.5 + textRadius * Math.cos(middleAngle)
                    var textY = height * 0.5 + textRadius * Math.sin(middleAngle)
                    //Dessiner le texte
                    ctx.fillStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? Constants.currentColorMode === Constants.ColorMode.DARK ? "#A1C9F2"
                                                                                                                                                                         : "#1677E6"
                                                                                                       : Constants.colorBlue
                    ctx.font = "bold " + textPixelSize + "px sans-serif"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.fillText(fichierAnalyse > 0 ? fichierAnalyse : "", textX, textY)

                }
            }
        }

        //Cercle fichiers sains
        Rectangle {
            id: fileSane
            anchors.centerIn: parent
            height: parent.height
            width: height
            color: "transparent"
            radius: width * 0.5
            border.color: Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#1677E6" : "#292929"
            border.width: parent.width * 0.01

            Canvas {
                id: circleSane
                anchors.fill: parent
                onPaint: {
                    var startAngle = -Math.PI * 0.5 + Math.PI * 2 * (fichierAnalyse / fichierTotal)
                    var endAngle = -Math.PI * 0.5 + Math.PI * 2 * ((fichierAnalyse + fichierSain) / fichierTotal)
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.beginPath()
                    ctx.strokeStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#00D400" : Constants.colorGreen
                    ctx.globalAlpha = 0.3
                    ctx.lineWidth = parent.width * 0.15
                    ctx.arc(width * 0.5,
                            height * 0.5,
                            width * 0.47 - ctx.lineWidth * 0.5,
                            startAngle,
                            endAngle)
                    ctx.stroke()

                    //Affichage du texte
                    ctx.globalAlpha = 1.0 //Reset de l'alpha avant affichage du texte
                    var textPixelSize = Math.min(parent.height * 0.1, parent.width * 0.1)
                    var middleAngle = (startAngle + endAngle) * 0.5
                    var textRadius = (width * 0.22) + (ctx.lineWidth * 0.70) + (textPixelSize * 0.5)
                    var textX = width * 0.5 + textRadius * Math.cos(middleAngle)
                    var textY = height * 0.5 + textRadius * Math.sin(middleAngle)
                    //Dessiner le texte
                    ctx.fillStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#00D400" : Constants.colorGreen
                    ctx.font = "bold " + textPixelSize + "px sans-serif"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.fillText(fichierSain > 0 ? fichierSain : "",
                                 textX,
                                 textY)
                }
            }
        }

        //Cercle fichiers infectés
        Rectangle {
            id: fileInfected
            anchors.centerIn: parent
            height: parent.height
            width: height
            color: "transparent"
            radius: width * 0.5
            border.color: Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#1677E6" : "#292929"
            border.width: parent.width * 0.01

            Canvas {
                id: circleInfected
                anchors.fill: parent
                onPaint: {
                    var startAngle = -Math.PI * 0.5 + Math.PI * 2 * ((fichierAnalyse + fichierSain) / fichierTotal)
                    var endAngle = -Math.PI * 0.5 + Math.PI * 2 * ((fichierAnalyse + fichierSain + fichierInfecte) / fichierTotal)
                    var arcWidth = parent.width * 0.15
                    var ctx = getContext("2d")
                    ctx.reset()

                    //Arc transparent
                    ctx.beginPath()
                    ctx.strokeStyle = Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#A61317" : Constants.colorRed
                    ctx.globalAlpha = 0.3
                    ctx.lineWidth = arcWidth
                    ctx.arc(width * 0.5,
                            height * 0.5,
                            width * 0.47 - ctx.lineWidth * 0.5,
                            startAngle,
                            endAngle)
                    ctx.stroke()

                    //Affichage du texte
                    ctx.globalAlpha = 1.0 //Reset de l'alpha avant affichage du texte
                    var textPixelSize = Math.min(parent.height * 0.1, parent.width * 0.1)
                    var middleAngle = (startAngle + endAngle) * 0.5
                    var textRadius = (width * 0.23) + (ctx.lineWidth * 0.70) + (textPixelSize * 0.5)
                    var textX = width * 0.5 + textRadius * Math.cos(middleAngle)
                    var textY = height * 0.5 + textRadius * Math.sin(middleAngle)
                    //Dessiner le texte
                    ctx.fillStyle = Constants.currentColorMode === Constants.ColorMode.LIGHT ? "#A61317" : Constants.currentColorMode === Constants.DARK ? "#D18287" : Constants.colorRed
                    ctx.font = "bold " + textPixelSize + "px sans-serif"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.fillText(fichierInfecte > 0 ? fichierInfecte : "", textX, textY)
                }
            }
        }

        //Cercle fichiers non analysés
        Rectangle {
            id: fileNotAnalysed
            anchors.centerIn: parent
            height: parent.height
            width: height
            color: "transparent"
            radius: width * 0.5
            border.color: Constants.currentColorMode !== Constants.ColorMode.STEALTH ? "#1677E6" : "#292929"
            border.width: parent.width * 0.01

            Canvas {
                id: circleNotAnalysed
                anchors.fill: parent
                onPaint: {
                    var startAngle = -Math.PI * 0.5 + Math.PI * 2 * ((fichierAnalyse + fichierSain + fichierInfecte) / fichierTotal)
                    var endAngle = -Math.PI * 0.5 + Math.PI * 2 * ((fichierAnalyse + fichierSain + fichierInfecte + fichierNonAnalyse) / fichierTotal)
                    var arcWidth = parent.width * 0.15
                    var ctx = getContext("2d")
                    ctx.reset()

                    //Arc transparent
                    ctx.beginPath()
                    ctx.strokeStyle = Constants.currentColorMode === Constants.ColorMode.LIGHT ? "#515151" : Constants.currentColorMode === Constants.ColorMode.DARK ? "#888" : "#3B3B3B"
                    ctx.globalAlpha = 0.5
                    ctx.lineWidth = arcWidth
                    ctx.arc(width * 0.5,
                            height * 0.5,
                            width * 0.47 - ctx.lineWidth * 0.5,
                            startAngle,
                            endAngle)
                    ctx.stroke()

                    //Affichage du texte
                    ctx.globalAlpha = 1.0 //Reset de l'alpha avant affichage du texte
                    var textPixelSize = Math.min(parent.height * 0.1, parent.width * 0.1)
                    var middleAngle = (startAngle + endAngle) * 0.5
                    var textRadius = (width * 0.23) + (ctx.lineWidth * 0.70) + (textPixelSize * 0.5)
                    var textX = width * 0.5 + textRadius * Math.cos(middleAngle)
                    var textY = height * 0.5 + textRadius * Math.sin(middleAngle)
                    //Dessiner le texte
                    ctx.fillStyle = Constants.currentColorMode === Constants.LIGHT ? "#58687D" : Constants.currentColorMode === Constants.DARK ? "#eee" : Constants.colorText
                    ctx.font = "bold " + textPixelSize + "px sans-serif"
                    ctx.textAlign = "center"
                    ctx.textBaseline = "middle"
                    ctx.fillText(fichierNonAnalyse > 0 ? fichierNonAnalyse : "",
                                 textX,
                                 textY)
                }
            }
        }

        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width
            height: parent.height
            spacing: 3

            Item {
                Layout.fillHeight: true
            }

            Text {
                text: fichierTotal
                Layout.alignment: Qt.AlignHCenter                
                /*anchors.centerIn: parent
                anchors.verticalCenterOffset: -parent.height * 0.1*/
                font.pixelSize: Math.min(parent.height * 0.2, parent.width * 0.2)
                font.bold: true
                color: Constants.colorText
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            Text {
                text: "fichiers"
                Layout.alignment: Qt.AlignHCenter
                /*anchors.centerIn: parent
                anchors.verticalCenterOffset: parent.height * 0.1*/
                font.pixelSize: Math.min(parent.height * 0.1, parent.width * 0.1)
                color: Constants.colorText
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            Item {
                Layout.fillHeight: true
            }
        }

        HelpTip {
            anchors.centerIn: parent
            libelle: "Progression de l'analyse"
            y: height *2/3
            x: width /-2
        }
    }    

    // Test roue état fichier
    // Timer {
    //     interval: 1000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         Constants.updateStateTracker(Constants.countNotAnalysedFiles+1,
    //                                          Constants.countAnalysingFiles+1,
    //                                          Constants.countSaneFiles+2,
    //                                          Constants.countInfectedFiles+1)
    //     }
    // }

}
