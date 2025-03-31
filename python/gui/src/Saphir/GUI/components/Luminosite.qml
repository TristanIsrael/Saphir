import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../imports"


Item {

    property int selectedMode: Constants.currentColorMode

    function chooseMode(mode)
    {
        console.log("Mode précédent :",  Constants.currentColorMode)
        console.log("Mode choisi :", mode)
        selectedMode = mode;
        switch(mode)
        {
        case 0:
            Constants.updateColorMode(Constants.ColorMode.LIGHT)
            break;
        case 1:
            Constants.updateColorMode(Constants.ColorMode.DARK)
            break;
        case 2:
            Constants.updateColorMode(Constants.ColorMode.STEALTH)
            break;
        case 3:
            //A modifier pour prendre en compte l'automatisme
            break;
        default:
            Constants.updateColorMode(Constants.ColorMode.DARK)
            break;
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

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Image {
                id: iconeClair
                source: selectedMode == 0 ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeClairActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeClairInactif.svg")
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                height:parent.height
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { chooseMode(0) }
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Image {
                id: iconeSombre
                source: selectedMode == 1 ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeSombreActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeSombreInactif.svg")
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                height:parent.height
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { chooseMode(1) }
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Image {
                id: iconeFurtif
                source: selectedMode == 2 ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeFurtifActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeFurtifInactif.svg")
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                height:parent.height
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { chooseMode(2) }
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Image {
                id: iconeAuto
                source: selectedMode == 3 ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeAutoActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "LuminositeAutoInactif.svg")
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                height:parent.height
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { chooseMode(3) }
            }
        }
    }
}
