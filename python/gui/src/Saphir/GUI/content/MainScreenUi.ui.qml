import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Effects
import Components
import Saphir

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
    property alias pnlFileSelection: pnlFileSelection
    property alias pnlStartStop: pnlStartStop
    property alias btnStartStop: btnStartStop
    property alias dlgAnalyseWholeStorage: dlgAnalyseWholeStorage

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
        id: topBar

        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }

        height: parent.height * 0.06
    }

    /* Lower left buttons */
    Panel {
        id: pnlMenuThemes

        x: btnLowVisibility.width * 0.25
        y: parent.height - ((height * 1.25) * 2)
        z: 100
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


                /*height: btnLowVisibility.width * 1.5
                spacing: btnLowVisibility.height * 0.3*/
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
        z: 100
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
    }

    /* Lower right buttons */
    Panel {
        id: pnlStartStop

        x: parent.width - (width * 1.25)
        y: parent.height - (height * 1.25)
        width: btnStartStop.width
        height: btnStartStop.height
        radius: height

        enabled: bindings.analysisReady && bindings.queueSize > 0

        RoundButton {
            id: btnStartStop
            flat: true
            icon: bindings.analyzing ? Constants.iconPause : Constants.iconStart
        }
    }

    /* Messages panel */
    MessagesPanel {
        id: messagesPanel

        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: parent.height * 0.05
        }

        visible: !bindings.ready || (bindings.ready && bindings.sourceName === "")
        radius: 10
    }

    /* Dialogs */
    MessageDialog {
        id: dlgConnectStorage

        anchors.centerIn: parent
        visible: bindings.ready && bindings.analysisReady
                 && bindings.sourceName === ""

        label: qsTr("Please connect a storage")
        buttonsLabels: []
    }

    MessageDialog {
        id: dlgAnalyseWholeStorage

        anchors.centerIn: parent
        visible: false

        label: qsTr("Do you want to analyze the whole storage?")
        buttonsLabels: ["Yes", "No"]
    }

    /* Main Panel */
    Item {
        anchors {
            top: topBar.bottom
            left: parent.left
            leftMargin: pnlMainMenu.x * 2 + btnMainMenu.width * 1.2
            right: pnlStartStop.left
            bottom: parent.bottom
            margins: root.height * 0.05
        }

        /* File selection */
        FilesSelectionPanel {
            id: pnlFileSelection
            anchors.fill: parent
            visible: false
        }

        /* Analysis */
        AnalysisPanel {
            id: pnlAnalysis
            anchors.fill: parent
            visible: bindings.ready && (bindings.analyzing || bindings.systemState === Enums.AnalysisCompleted)
        }
    }

    Bindings {
        id: bindings
    }
}
