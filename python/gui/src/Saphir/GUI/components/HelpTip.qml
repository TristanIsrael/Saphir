import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import "../imports"

Popup {
    id: root

    property alias libelle: lbl.text

    visible: Constants.afficherAide

    background: Item {}
    closePolicy: Popup.NoAutoClose

    x: 10
    y: 10

    Rectangle {
        id: bkg

        radius: height*0.2
        width: lbl.width *1.1
        height: lbl.height *1.2

        Text {
            id: lbl
            color: "black"
            text: "Ceci est une aide\nsur plusieurs lignes"
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
            anchors.centerIn: parent
        }
    }

    DropShadow {
        anchors.fill: bkg
        radius: 6
        color: "#333"
        source: bkg
        cached: true
    }


}
