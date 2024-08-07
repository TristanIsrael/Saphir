import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

GridLayout {
    id: lyt

    property int infected: 99
    property int clean: 99

    rows: 1
    columns: 2
    columnSpacing: height / 2

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 300
    implicitHeight: 100

    Text {
        id: lblInfectedFiles
        text: infected
        color: Constants.alertColor
        Layout.fillHeight: true
        Layout.fillWidth: true
        horizontalAlignment: Qt.AlignRight
        verticalAlignment: Qt.AlignVCenter
        fontSizeMode: Text.Fit
        font {
            family: "Alien Encounters"
            pixelSize: height
        }
    }

    Text {
        id: lblCleanFiles
        text: clean
        color: Constants.successColor
        Layout.fillHeight: true
        Layout.fillWidth: true
        horizontalAlignment: Qt.AlignLeft
        verticalAlignment: Qt.AlignVCenter
        fontSizeMode: Text.Fit
        font {
            family: "Alien Encounters"
            pixelSize: height
        }
    }
}
