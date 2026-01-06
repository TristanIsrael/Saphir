import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import "../imports"

Item {
    id: root
    property string libelle: "Réinitialisation du système en cours,\nveuillez patienter."

    implicitWidth: 500
    implicitHeight: 300

    Item {
        anchors.fill: parent

        Item {
            anchors.fill: parent

            Rectangle {
                id: bkg
                anchors.fill: parent
                radius: 10
            }

            DropShadow {
                anchors.fill: bkg
                radius: 6
                color: "#333" //Constants.colorText
                source: bkg
                cached: true
            }
        }
    }

    Rectangle {
        anchors.fill: parent

        radius: bkg.radius
        border {
            color: "#505a6d"
            width: 4
        }

        color: Constants.currentColorMode === Constants.LIGHT ? "#eee" : Constants.currentColorMode === Constants.DARK ? "#606b81" : "#272727"

        ColumnLayout {
            id: lyt

            anchors {
                fill: parent
                margins: 20
            }

            Item {
                Layout.fillHeight: true
            }

            Label {
                id: lblLibelle
                color: Constants.colorText
                text: root.libelle
                font.pixelSize: 24
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }
}
