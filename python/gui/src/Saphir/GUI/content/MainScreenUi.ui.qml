import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components

Item {
    id: mainWindow

    property alias back: back

    /* Bindings */
    property bool ready: false
    property bool running: false

    /* Private properties */
    implicitWidth: 1344
    implicitHeight: 768
    width: implicitWidth
    height: implicitHeight

    Item {
        id: back
        anchors.fill: parent
        layer.enabled: true

        Image {
            anchors.fill: parent
            source: "images/back.png"
            fillMode: Image.PreserveAspectCrop
            //layer.enabled: true
        }
    }

    TopBar {
        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }
    }

    /* Lower left buttons */
    RoundButton {
        id: btnTheme
        visible: true

        x: width * 0.25
        y: parent.height - (height * 1.25) * 2 - 20

        icon: Constants.iconThemeLight
    }

    RoundButton {
        id: btnMenu

        x: width * 0.25
        y: parent.height - (height * 1.25)

        icon: Constants.iconMenu
    }

    /* Lower right buttons */
    RoundButton {
        id: btnStartStop

        x: parent.width - (width * 1.25)
        y: parent.height - (height * 1.25)

        icon: mainWindow.running ? Constants.iconPause : Constants.iconStart
        outlined: false
        enabled: mainWindow.ready
    }

    /* Initial dialog */


    /*MessageDialog {
        id: dlg
        anchors.centerIn: parent
    }*/


    /*RoundButton {
        anchors.centerIn: parent

        icon: Constants.iconThemeLight
        width: 300
        height: 300
    }*/
}
