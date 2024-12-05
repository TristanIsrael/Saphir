import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

GridLayout {
    id: lyt

    rows: 1
    columns: 3
    columnSpacing: height / 2

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 400
    implicitHeight: 100

    Text {
        id: lblInfectedFiles
        text: ApplicationController.infectedFilesCount
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
        id: lblTotalFiles
        text: ApplicationController.totalFilesCount
        color: Constants.textColor
        Layout.fillHeight: true
        Layout.fillWidth: true
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        fontSizeMode: Text.Fit
        font {
            family: "Alien Encounters"
            pixelSize: height*0.7
        }
    }

    Text {
        id: lblCleanFiles
        text: ApplicationController.cleanFilesCount
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
