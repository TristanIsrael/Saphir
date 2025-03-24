import QtQuick
import QtQuick.Controls
import "../../imports"


Rectangle {
    color:"transparent"
    property string label: Constants.outputUSBName
    property bool selected: Constants.isOutputUSBPlugged

    Connections {
        target: Constants
        onOutputSUBPlugged: {
            Constants.isOutputUSBPlugged = true
            Constants.outputUSBName = usbName
        }
        onOutputUSBUnplugged: {
            Constants.isOutputUSBPlugged = false
            Constants.outputUSBName = ""
        }
    }

    Image {
        source: selected ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "SupportSortieConnecte.svg")
                         : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "SupportSortieNonConnecte.svg")
        fillMode: Image.PreserveAspectFit
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height:parent.height

        Rectangle {
            color: "transparent"
            anchors.right: parent.right
            anchors.rightMargin: parent.width * 0.04
            anchors.topMargin: parent.height
            width: parent.width * 0.75
            height: parent.height * 0.20
            y: parent.height * 0.42
            Label
            {
                color: Constants.colorText
                text: label
                width: parent.width
                height: parent.height
                anchors.left: parent.left
                anchors.leftMargin: parent.width * 0.05
                anchors.verticalCenter: parent.verticalCenter
                wrapMode: Text.WordWrap
                font.pointSize: Math.max(10, Math.min(40, parent.width / text.length * 2))
                font.pixelSize: Math.min(parent.height, parent.width)
                elide: Text.ElideRight
            }
        }
    }

    // //Test de changement de status
    // property bool actionT: false
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         actionT = !actionT
    //         if(actionT)
    //             Constants.outputSUBPlugged("Clé usb 2GO")
    //         else
    //             Constants.outputUSBUnplugged()
    //     }
    // }
}
