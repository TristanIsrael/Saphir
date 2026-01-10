import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Effects
import Components

Item {
    id: mainWindow

    property alias back: back
    property alias backFilter: backFilter
    property alias pnlMenuThemes: pnlMenuThemes
    property alias btnLowVisibility: btnLowVisibility
    property alias btnDark: btnDark
    property alias btnLight: btnLight
    property alias pnlMainMenu: pnlMainMenu
    property alias btnMainMenu: btnMainMenu
    property alias btnHelp: btnHelp
    property alias btnSystemState: btnSystemState
    property alias btnLog: btnLog
    property alias btnRestart: btnRestart
    property alias btnShutdown: btnShutdown

    property bool menuThemesOpened: false
    property bool mainMenuOpened: false

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
            id: imgBack
            anchors.fill: parent
            source: "images/3535287.jpg"
            fillMode: Image.PreserveAspectCrop
        }

        MultiEffect {
            id: backFilter
            anchors.fill: parent
            source: imgBack
            saturation: 0
            colorization: 1.0
            colorizationColor: Environment.colorFilterNotReady
        }
    }

    TopBar {
        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }

        height: parent.height * 0.05
    }

    /* Lower left buttons */
    Panel {
        id: pnlMenuThemes

        x: btnLowVisibility.width * 0.25
        y: parent.height - ((height * 1.25) * 2)
        height: lytMenuThemes.height
        width: mainWindow.menuThemesOpened ? lytMenuThemes.width : btnLowVisibility.width * 1.5
        clip: false
        highlight: false
        radius: mainWindow.menuThemesOpened ? 10 : height

        RowLayout {
            id: lytMenuThemes
            height: btnLowVisibility.width * 1.5
            spacing: btnLowVisibility.height * 0.3

            Item {}

            RoundButton {
                id: btnLowVisibility
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconThemeLowVisibility
                flat: true
                visible: mainWindow.menuThemesOpened
                         || Environment.theme === Constants.lowVisibility
            }

            RoundButton {
                id: btnDark
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconThemeDark
                flat: true
                visible: mainWindow.menuThemesOpened
                         || Environment.theme === Constants.dark
            }

            RoundButton {
                id: btnLight
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconThemeLight
                flat: true
                visible: mainWindow.menuThemesOpened
                         || Environment.theme === Constants.light
            }

            Item {}
        }
    }

    Panel {
        id: pnlMainMenu

        x: btnShutdown.width * 0.25
        y: parent.height - (height * 1.25)
        height: lytMainMenu.height
        width: mainWindow.mainMenuOpened ? lytMainMenu.width : btnShutdown.width * 1.5
        clip: false
        highlight: false
        radius: mainWindow.mainMenuOpened ? 10 : height

        RowLayout {
            id: lytMainMenu
            height: btnMainMenu.width * 1.5
            spacing: btnMainMenu.height * 0.3

            Item {}

            RoundButton {
                id: btnMainMenu
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconMenu
                flat: true
            }

            RoundButton {
                id: btnHelp
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconHelp
                flat: true
                visible: mainWindow.mainMenuOpened
            }

            RoundButton {
                id: btnSystemState
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconSystemState
                flat: true
                visible: mainWindow.mainMenuOpened
            }

            RoundButton {
                id: btnLog
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconLog
                flat: true
                visible: mainWindow.mainMenuOpened
            }

            RoundButton {
                id: btnRestart
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconRestart
                flat: true
                visible: mainWindow.mainMenuOpened
            }

            RoundButton {
                id: btnShutdown
                Layout.alignment: Qt.AlignHCenter
                icon: Constants.iconShutdown
                flat: true
                visible: mainWindow.mainMenuOpened
            }

            Item {}
        }
    }

    /* Lower right buttons */
    Panel {
        id: pnlStartStop

        x: parent.width - (width * 1.25)
        y: parent.height - (height * 1.25)
        width: btnStartStop.width
        height: btnStartStop.height
        radius: height

        //flat: true
        //icon: bindings.running ? Constants.iconPause : Constants.iconStart
        enabled: bindings.ready

        RoundButton {
            id: btnStartStop
            flat: true
            width: 100
            height: 100
            icon: bindings.running ? Constants.iconPause : Constants.iconStart
        }
    }

    /* Messages panel */
    MessagesPanel {
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: parent.height * 0.05
        }

        visible: !bindings.running
        radius: 10
    }

    /* Initial dialog */
    MessageDialog {
        id: dlg
        anchors.centerIn: parent
        visible: bindings.ready && bindings.sourceName === ""

        label: qsTr("Please connect a storage")
        buttonsLabels: []
    }

    Bindings {
        id: bindings
    }
}
