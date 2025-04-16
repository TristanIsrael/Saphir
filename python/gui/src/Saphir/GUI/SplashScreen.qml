import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "imports"

Rectangle {
    id: coreSplashScreen

    property string progressText: "Chargement..."

    Connections {
        target: Constants
        onUpdateSplashScreenText: {
            progressText: newText
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.centerIn: parent
        Image {
            anchors.fill: parent
            anchors.centerIn: parent
            source: Qt.resolvedUrl(Constants.colorModePath  + "SplashScreen.png")
            fillMode: Image.Stretch
        }

        BusyIndicator {
            width: parent.width * 0.05
            height: parent.height * 0.075
            anchors.centerIn: parent
            anchors.verticalCenterOffset: parent.height * 0.35
            running: true

            Rectangle {
                anchors.top: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width * 5
                height: parent.height
                color: "transparent"
                Label {
                    id: textHolder
                    anchors.centerIn: parent
                    width: parent.width
                    height: parent.height
                    text: progressText
                    color: Constants.colorText
                    font.pixelSize: Math.min(height * 0.4, width * 0.15)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Label.ElideRight
                }
            }
        }
    }

    Timer { //Ce timer est à supprimer si le back gère
        interval: 500
        running: true
        repeat: false
        onTriggered: {
            parent.visible = false
        }
    }
}
