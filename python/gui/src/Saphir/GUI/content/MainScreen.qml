import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components

Window {
    id: root

    /* Internal properties */
    width: 1200
    height: 700
    visible: true
    title: "SAPHIR"

    MainScreenUi {
        id: window

        anchors.fill: parent        

        backFilter.colorizationColor: bindings.systemStateColor

        /* Slots */
        Connections {
            target: window.btnDark

            onClicked: function() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLight

            onClicked: function() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLowVisibility

            onClicked: function() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnMainMenu

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnHelp

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnSystemState

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnLog

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnRestart

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnShutdown

            onClicked: function() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        /* Animations */
        Behavior on pnlMenuThemes.width {
            PropertyAnimation {
                duration: 200
                easing.type: Easing.OutCubic
            }
        }

        Behavior on pnlMainMenu.width {
            PropertyAnimation {
                duration: 200
                easing.type: Easing.OutCubic
            }
        }

    }

    Bindings {
        id: bindings
    }

    /* Testing only */
    Component.onCompleted: {
    }
}

