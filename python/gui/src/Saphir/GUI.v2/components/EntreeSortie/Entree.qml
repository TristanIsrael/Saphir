import QtQuick
import QtQuick.Controls
import "../../imports"
import "../../components"
import net.alefbet

Item {    
    property string label: Constants.inputUSBName
    property bool selected: Constants.isInputUSBPlugged

    /*Connections {
        target: Constants

        onInputUSBPlugged: {
            Constants.isInputUSBPlugged = true
            Constants.inputUSBName = usbName
        }
        onInputUSBUnplugged: {
            Constants.isInputUSBPlugged = false
            Constants.inputUSBName = ""
        }
    }*/

    Image {
        id: image
        source: selected ? Qt.resolvedUrl(Constants.colorModePath  + "SupportEntreeConnecte.svg")
                         : Qt.resolvedUrl(Constants.colorModePath  + "SupportEntreeNonConnecte.svg")
        fillMode: Image.PreserveAspectFit
        width: parent.width
        height: parent.height
        horizontalAlignment: Image.AlignLeft
        verticalAlignment: Image.AlignVCenter

        Item {
            anchors.left: parent.left
            anchors.leftMargin: parent.width * 0.025
            anchors.topMargin: parent.height
            width: parent.width * 0.7
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
        libelle: "Nom du support source"
        visible: Constants.afficherAide && ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection && parent.visible
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
    //             Constants.inputUSBPlugged("Clé usb 2GO")
    //         else
    //             Constants.inputUSBUnplugged()
    //     }
    // }
}
