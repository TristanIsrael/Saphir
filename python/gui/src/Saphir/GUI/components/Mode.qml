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
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "EncartSelectionLuminosite.svg")
        anchors.fill: parent
    }*/
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        radius: height
        border {            
            width: 1.5
            color: Constants.currentColorMode === Constants.LIGHT ? "#848484" : Constants.currentColorMode === Constants.DARK ? "#66788F" : "#272727"
        }        
    }
    RowLayout
    {
        anchors.fill: parent
        anchors.leftMargin: width * 0.10
        anchors.rightMargin: width * 0.10
        anchors.topMargin: height * 0.10
        anchors.bottomMargin: height * 0.10
        Item
        {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Image {
                source : selectedMode == 0 ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModeEcranPCActif.svg")
                                           : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModeEcranPCInactif.svg")
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
                source: selectedMode == 1 ?  Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModePCPortableActif.svg")
                                          :  Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModePCPortableInactif.svg")
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
                source: selectedMode == 2 ?  Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModeVehiculeActif.svg")
                                          :  Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ModeVehiculeInactif.svg")
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
}

