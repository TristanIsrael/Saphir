import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Saphir

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

            function onClicked() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLight

            function onClicked() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLowVisibility

            function onClicked() {
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnMainMenu

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnHelp

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnSystemState

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnLog

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnRestart

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: window.btnShutdown

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
            }
        }

        Connections {
            target: ApplicationController

            function onSourceReadyChanged() {
                if(ApplicationController.sourceReady) {
                    window.dlgAnalyseWholeStorage.visible = true
                }                
            }
        }

        Connections {
            target: window.dlgAnalyseWholeStorage

            function onRejected() {
                bindings.setAnalysisMode(Enums.AnalyseSelection)
                window.pnlFileSelection.visible = true
                window.dlgAnalyseWholeStorage.visible = false
            }

            function onAccepted() {
                bindings.setAnalysisMode(Enums.AnalyseWholeSource)
                window.dlgAnalyseWholeStorage.visible = false
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
        // Verify whether a storage is connected
        if(ApplicationController.sourceReady) {
            window.dlgAnalyseWholeStorage.visible = true
        }
    }
}

