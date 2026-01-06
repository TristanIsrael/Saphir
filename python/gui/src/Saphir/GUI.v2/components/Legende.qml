import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../imports"


RowLayout
{
    property double fontSize: 0.5
    property double margin: 0.01

    //height: parent.height
    //anchors.horizontalCenter: parent.horizontalCenter
    Image
    {
        source: Qt.resolvedUrl(Constants.colorModePath  + "LegendeSain.svg")
        fillMode: Image.PreserveAspectFit
        Layout.fillHeight: true
    }
    Label
    {
        Layout.fillHeight: true
        text: "Sain"
        color: Constants.colorText
        font.pixelSize: height * fontSize
        verticalAlignment: Text.AlignVCenter
        Layout.rightMargin: parent.width * margin
    }
    Image {
        source: Qt.resolvedUrl(Constants.colorModePath  + "LegendeNonTraite.svg")
        fillMode: Image.PreserveAspectFit
        Layout.fillHeight: true
    }
    Label
    {
        Layout.fillHeight: true
        text: "Non traité"
        color: Constants.colorText
        font.pixelSize: height * fontSize
        verticalAlignment: Text.AlignVCenter
        Layout.rightMargin: parent.width * margin
    }
    Image {
        source: Qt.resolvedUrl(Constants.colorModePath  + "LegendeInfecte.svg")
        fillMode: Image.PreserveAspectFit
        Layout.fillHeight: true
    }
    Label
    {
        Layout.fillHeight: true
        text: "Infectés"
        color: Constants.colorText
        font.pixelSize: height * fontSize
        verticalAlignment: Text.AlignVCenter
        Layout.rightMargin: parent.width * margin
    }
    /*Image {
        source: Qt.resolvedUrl(Constants.colorModePath  + "LegendeEnCoursAnalyse.svg")
        fillMode: Image.PreserveAspectFit
        Layout.fillHeight: true
    }
    Label
    {
        Layout.fillHeight: true
        text: "En cours d'analyse"
        color: Constants.colorText
        font.pixelSize: height * fontSize
        verticalAlignment: Text.AlignVCenter
    }*/
}
