import QtQuick
import QtQuick.Controls
import "../../imports"
import "../../components"

Item {

    property string label: Constants.outputUSBName
    property bool selected: Constants.isOutputUSBPlugged

    Image {
        source: selected ? Qt.resolvedUrl(Constants.colorModePath  + "SupportSortieConnecte.svg")
                         : Qt.resolvedUrl(Constants.colorModePath  + "SupportSortieNonConnecte.svg")
        fillMode: Image.PreserveAspectFit
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height:parent.height

        Item {
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

    HelpTip {
        anchors.centerIn: parent
        libelle: "Nom du support cible"
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
