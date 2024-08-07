import QtQuick
import QtQuick.Controls

Rectangle {
    id: entete

    property alias lblCurrentTime: lblCurrentTime

    height: implicitHeight
    width: implicitWidth
    implicitWidth: 900
    implicitHeight: 40
    color: Constants.contrastColor

    Text {
        id: mention
        text: qsTr("Niveau max : DR")
        anchors {
            verticalCenter: parent.verticalCenter
        }
        x: 8
        font {
            family: "Avenir Next"
            pixelSize: parent.height * 0.5
            weight: Font.DemiBold
            capitalization: Font.SmallCaps
        }
        color: Constants.alertColor
    }

    Text {
        text: qsTr("Panoptiscan")
        anchors.centerIn: parent
        font {
            family: "freshbot"
            pixelSize: parent.height
        }
        color: Constants.titleColor
    }

    Text {
        id: lblCurrentTime

        anchors {
            right: parent.right
            rightMargin: 8
            verticalCenter: parent.verticalCenter
        }
        font {
            family: "Avenir Next"
            pixelSize: parent.height * 0.5
            weight: Font.Medium
        }

        text: "17:10"
    }
}
