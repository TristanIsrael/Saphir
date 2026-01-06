import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components

Item {
    id: root

    implicitWidth: 1200
    implicitHeight: 900
    width: implicitWidth
    height: implicitHeight

    Image {
        id: back
        anchors.fill: parent
        source: "images/back.jpg"
        fillMode: Image.Stretch
    }

    Panel {
        id: pnl
        anchors {
            fill: parent
            margins: 0
        }


        /*width: parent.width/3
        height: parent.height*0.8
        anchors.centerIn: parent*/

        //glassColor: "#821e1e1e"
        //glassColor: "#4deef3f8"
        //glassColor: "#71eef3f8"
        //glassColor: "#52eef3f8"
        // opacité : #71 - #82
        glassColor: "#444480"
        blurRadius: 25
        borderRadius: 0
        borderWidth: 0
        //borderRadius: height/12
        borderColor: "#aaf7fdfa"
        backgroundSource: back
        highlight: true

        // Top Bar
        TopBar {
            anchors {
                left: parent.left
                right: parent.right
            }

            height: root.height / 10
        }

        // Bouton de test
        Rectangle {
            id: btn
            color: "#bb3c5a7c"
            width: 200
            height: 50
            anchors.centerIn: parent
            radius: height / 5

            border {
                width: 1
                color: "#ff3c5a7c"
            }

            Text {
                anchors.centerIn: parent
                text: "Tester"
                color: "#aaf7fdfa"
                font.pixelSize: parent.height * 0.7
                fontSizeMode: Text.HorizontalFit
            }
        }
    }
}
