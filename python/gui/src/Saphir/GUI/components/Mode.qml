import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../imports"


Item
{
    property int selectedMode: Constants.currentDisplayMode

    function chooseMode(mode)
    {
        if (Constants.currentDisplayMode !== mode)
        {
            Constants.currentDisplayMode = mode
            Constants.changeDisplayMode(Constants.currentDisplayMode)
        }
    }

    /*Image {
        source: Qt.resolvedUrl(Constants.colorModePath  + "EncartSelectionLuminosite.svg")
        anchors.fill: parent
    }*/
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        radius: height
        border {            
            width: 2
            color: Constants.currentColorMode === Constants.LIGHT ? "#848484" : Constants.currentColorMode === Constants.DARK ? "#66788F" : "#272727"
        }        
    }

    RowLayout
    {
        anchors {
            fill: parent
            margins: parent.height/10
        }

        Item
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Image {
                source : selectedMode == 0 ? Qt.resolvedUrl(Constants.colorModePath  + "ModeEcranPCActif.svg")
                                           : Qt.resolvedUrl(Constants.colorModePath  + "ModeEcranPCInactif.svg")
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                height:parent.height
            }
            MouseArea
            {
                anchors.fill: parent
                onClicked: { chooseMode(0) }
            }
        }
        Item
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Image {
                source: selectedMode == 1 ?  Qt.resolvedUrl(Constants.colorModePath  + "ModePCPortableActif.svg")
                                          :  Qt.resolvedUrl(Constants.colorModePath  + "ModePCPortableInactif.svg")
                fillMode: Image.PreserveAspectFit
                height:parent.height
                anchors.horizontalCenter: parent.horizontalCenter
            }
            MouseArea
            {
                anchors.fill: parent
                onClicked: { chooseMode(1) }
            }
        }
        Item
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Image {
                //source: selectedMode == 2 ? "../images/Icone Mode Mobile-UP.svg"
                //                          : "../images/Icone Mode Mobile.svg"
                source: selectedMode == 2 ?  Qt.resolvedUrl(Constants.colorModePath  + "ModeVehiculeActif.svg")
                                          :  Qt.resolvedUrl(Constants.colorModePath  + "ModeVehiculeInactif.svg")
                fillMode: Image.PreserveAspectFit
                height:parent.height
                anchors.horizontalCenter: parent.horizontalCenter
            }
            MouseArea
            {
                anchors.fill: parent
                onClicked: { chooseMode(2) }
            }
        }
    }

    HelpTip {
        libelle: "Inutilisé"
    }
}

