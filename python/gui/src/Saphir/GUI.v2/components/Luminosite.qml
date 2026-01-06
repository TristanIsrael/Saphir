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
        source: Qt.resolvedUrl(Constants.colorModePath  + "EncartSelectionLuminosite.svg")
        anchors.fill: parent
    }*/
    Rectangle {
        anchors.fill: parent
        color: "transparent" //"#445060"
        radius: height

        border {            
            width: 2
            color: Constants.currentColorMode === Constants.LIGHT ? "#848484" : Constants.currentColorMode === Constants.DARK ? "#70839c" : "#272727"
        }        
    }

    RowLayout
    {
        anchors {
            fill: parent
            margins: parent.height/10
        }
        spacing: height/2

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Image {
                id: iconeClair
                source: selectedMode == 0 ? Qt.resolvedUrl(Constants.colorModePath  + "LuminositeClairActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath  + "LuminositeClairInactif.svg")
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
                source: selectedMode == 1 ? Qt.resolvedUrl(Constants.colorModePath  + "LuminositeSombreActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath  + "LuminositeSombreInactif.svg")
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
                source: selectedMode == 2 ? Qt.resolvedUrl(Constants.colorModePath  + "LuminositeFurtifActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath  + "LuminositeFurtifInactif.svg")
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
                source: selectedMode == 3 ? Qt.resolvedUrl(Constants.colorModePath  + "LuminositeAutoActif.svg")
                                          : Qt.resolvedUrl(Constants.colorModePath  + "LuminositeAutoInactif.svg")
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

    HelpTip {
        libelle: "Basculer entre les thèmes d'affichages"
    }
}
