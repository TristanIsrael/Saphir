import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Effects
import Components
import Saphir

Item {
    id: mainWindow

    property alias back: back
    property alias imgBack: imgBack
    //property alias backFilter: backFilter
    property alias pnlMenuThemes: pnlMenuThemes
    property alias btnLowVisibility: btnLowVisibility
    property alias btnDark: btnDark
    property alias btnLight: btnLight
    property alias pnlMainMenu: pnlMainMenu
    property alias btnMainMenu: btnMainMenu
    property alias btnHelp: btnHelp
    property alias btnRestart: btnRestart
    property alias btnShutdown: btnShutdown
    property alias pnlFileSelection: pnlFileSelection
    property alias dlgShutdown: dlgShutdown
    property alias dlgRestart: dlgRestart
    property alias lytMenuThemes: lytMenuThemes
    property alias lytMenuLanguages: lytMenuLanguages
    property alias btnLanguageEN: btnLanguageEN
    property alias btnLanguageFR: btnLanguageFR
    property alias pnlViewer: pnlViewer

    property bool menuThemesOpened: false
    property bool mainMenuOpened: false
    property bool menuLanguagesOpened: false
    property string language: "This is a string"

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
            source: Environment.backgroundImage
            fillMode: Image.PreserveAspectCrop
        }

        MultiEffect {
            id: backFilter
            anchors.fill: parent
            visible: Environment.theme === Constants.lowVisibility
            source: imgBack
            brightness: -0.5
        }
    }

    TopBar {
        id: topBar

        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }

        height: parent.height * 0.06
    }

    /* Upper left buttons */
    Panel {
        id: pnlMenuLanguages

        x: btnLanguageEN.width * 0.25
        y: topBar.height * 2
        z: 99
        height: lytMenuLanguages.height
        width: mainWindow.menuLanguagesOpened ? lytMenuLanguages.width : btnLanguageEN.width * 1.2
        clip: false
        highlight: false
        radius: height

        Item {
            // For clipping
            width: pnlMenuLanguages.width
            height: pnlMenuLanguages.height
            clip: true

            RowLayout {
                id: lytMenuLanguages
                height: btnLanguageEN.width * 1.2
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: btnLanguageEN.width * 0.05
                }

                Item {}

                RoundButton {
                    id: btnLanguageEN
                    Layout.alignment: Qt.AlignHCenter
                    icon: "EN"
                    symbol: false
                    flat: true
                    visible: mainWindow.menuLanguagesOpened || language === ""
                }

                RoundButton {
                    id: btnLanguageFR
                    Layout.alignment: Qt.AlignHCenter
                    icon: "FR"
                    symbol: false
                    flat: true
                    visible: mainWindow.menuLanguagesOpened || language === "fr"
                }

                Item {}
            }
        }
    }

    /* Lower left buttons */
    Panel {
        id: pnlMenuThemes

        x: btnLowVisibility.width * 0.25
        y: parent.height - ((height * 1.25) * 2)
        z: 99
        height: lytMenuThemes.height
        width: mainWindow.menuThemesOpened ? lytMenuThemes.width : btnLowVisibility.width * 1.2
        clip: false
        highlight: false
        radius: height

        Item {
            // For clipping
            width: pnlMenuThemes.width
            height: pnlMenuThemes.height
            clip: true

            RowLayout {
                id: lytMenuThemes
                height: btnLowVisibility.width * 1.2
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: btnLowVisibility.width * 0.05
                }

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
    }

    Panel {
        id: pnlMainMenu

        x: btnShutdown.width * 0.25
        y: parent.height - (height * 1.25)
        z: 99
        height: lytMainMenu.height
        width: mainWindow.mainMenuOpened ? lytMainMenu.width : btnShutdown.width * 1.2
        clip: false
        highlight: false
        radius: height

        Item {
            // For clipping
            width: pnlMainMenu.width
            height: pnlMainMenu.height
            clip: true

            RowLayout {
                id: lytMainMenu
                height: btnMainMenu.width * 1.2
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: btnMainMenu.width * 0.05
                }

                //spacing: btnMainMenu.height * 0.3
                Item {}

                RoundButton {
                    id: btnMainMenu

                    Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
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
    }

    MessageDialog {
        id: dlgRestart

        anchors.centerIn: parent
        visible: false

        label: qsTr("Do you want to clean the system?")
        buttonsLabels: [qsTr("Yes"), qsTr("No")]
        handheld: bindings.handheld
    }

    MessageDialog {
        id: dlgShutdown

        anchors.centerIn: parent
        visible: false

        label: qsTr("Do you want to shutdown the system?")
        buttonsLabels: [qsTr("Yes"), qsTr("No")]
        handheld: bindings.handheld
    }

    /* Main Panel */
    Item {
        anchors {
            top: topBar.bottom
            left: parent.left
            leftMargin: pnlMainMenu.x * 2 + btnMainMenu.width * 1.2
            right: parent.right
            bottom: parent.bottom
            margins: mainWindow.height * 0.05
        }

        /* File selection */
        FilesSelectionPanel {
            id: pnlFileSelection
            anchors.fill: parent
            visible: true
        }

        ViewerPanel {
            id: pnlViewer
            anchors.fill: parent
            visible: false
        }

    }

    Bindings {
        id: bindings
    }
}
