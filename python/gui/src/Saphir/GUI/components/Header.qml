import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../imports"


Rectangle
{
    property double fontSize: 0.5
    id: header
    color: "transparent"

    function getLoadingImage() {
        if (Constants.batteryLevel < 0.33)
            return Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Batterie0Barre.svg")
        else if (Constants.batteryLevel < 0.66)
            return Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Batterie1Barre.svg")
        else if (Constants.batteryLevel < 0.85)
            return Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Batterie2Barres.svg")
        else
            return Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Batterie3Barres.svg")
    }

    Connections {
        target: Constants
        onUpdateBatteryLevel: {
            Constants.batteryLevel = newBatteryLevel
        }
        onDeviceWired: {
            Constants.isWired = isDeviceWired
        }
    }

    Image {
        id: background
        width: parent.width
        height: parent.height
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "BarreEtat.svg")
        fillMode: Image.Stretch
        anchors.fill: parent
    }
    RowLayout
    {
        anchors.fill: parent
        spacing: 0
        anchors.leftMargin: 0.016 * parent.width
        anchors.rightMargin: 0.016 * parent.width

        Label
        {
            id: timeLabel
            color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? "1E1E1E" : "white"
            text: "HH:mm:ss Z"
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredWidth: 30
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            font.pixelSize: height * fontSize
        }
        Timer
        {
            triggeredOnStart: true
            interval: 1000 // Mise à jour toutes les secondes
            running: true
            repeat: true
            onTriggered: {
                timeLabel.text = Qt.formatTime(new Date(), "HH:mm:ss Z");
            }
        }

        Label
        {
            color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? "1E1E1E" : "white"
            text: "Diffusion Restreinte"
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredWidth: 60
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            font.pixelSize: height * fontSize
            font.bold: true
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
        }

        RowLayout {

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.preferredWidth: 10
            Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
            Layout.bottomMargin: height * 0.2
            Layout.topMargin: height * 0.2
            //spacing: 0

            Image {
                source: Constants.isWired ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeEnCharge_Actif.svg")
                                              : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeEnCharge_Inactif.svg")
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                horizontalAlignment: Image.AlignRight
                Layout.bottomMargin: height * 0.2
                Layout.topMargin: height * 0.2
                fillMode: Image.Stretch
            }

            Label {
                Layout.fillHeight: true
                Layout.fillWidth: true
                visible: Constants.isWired
                text: "/"
                color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? "1E1E1E" : "white"
                horizontalAlignment: Label.AlignHCenter
                verticalAlignment: Label.AlignVCenter
                font.pixelSize: height * fontSize
            }

            RowLayout {
                id: batteryState
                Layout.fillHeight: true
                Layout.fillWidth: true
                Label {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    text: Math.round(Constants.batteryLevel * 100.0) + "%"
                    color: Constants.currentColorMode == Constants.ColorMode.STEALTH ? "1E1E1E" : "white"
                    horizontalAlignment: Label.AlignHCenter
                    verticalAlignment: Label.AlignVCenter
                    font.pixelSize: height * fontSize
                }

                Image {
                    source: getLoadingImage()
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    horizontalAlignment: Image.AlignHCenter
                    Layout.bottomMargin: height * 0.2
                    Layout.topMargin: height * 0.2
                    fillMode: Image.Stretch
                }
            }

        }
    }

    Image {
        id: appLogo
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LogoSAPHIR.svg")
        //width: parent.width * 0.085
        height: parent.height * 4
        x: (parent.width * 0.5295) + (width * 0.5)
        y: parent.height * -0.05
        fillMode: Image.PreserveAspectFit

        Image {
            id: appName
            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "TexteSAPHIR.svg")
            //width: parent.width * 1.2
            height: parent.height * 0.25
            fillMode: Image.PreserveAspectFit
            y: parent.height + (parent.height * -0.05)
            //anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    // Timer {
    //     interval: 100
    //     running: true
    //     repeat: true
    //     onTriggered: {
    //         Constants.updateBatteryLevel(Constants.batteryLevel + 0.01)
    //     }
    // }
}
