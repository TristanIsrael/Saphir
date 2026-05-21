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

        language: ApplicationController.language
        backFilter.colorizationColor: bindings.systemStateColor
        imgBack.source: {
            if(Environment.theme === Constants.light) {
                if(bindings.infected) {
                    return Environment.systemInfectedImage
                } else if(bindings.used) {
                    return Environment.systemUsedImage
                } else if(bindings.ready) {
                    return Environment.systemReadyImage
                }
            }

            return Environment.backgroundImage
        }

        /* Slots */
        Connections {
            target: window.btnDark

            function onClicked() {
                Environment.theme = Constants.dark
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLight

            function onClicked() {
                Environment.theme = Constants.light
                window.menuThemesOpened = !window.menuThemesOpened
            }
        }

        Connections {
            target: window.btnLowVisibility

            function onClicked() {
                Environment.theme = Constants.lowVisibility
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
                window.dlgSystemState.visible = true
            }
        }

        Connections {
            target: window.btnLog

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
                window.dlgLog.visible = true
            }
        }

        Connections {
            target: window.btnRestart

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
                window.dlgRestart.visible = true
            }
        }

        Connections {
            target: window.btnShutdown

            function onClicked() {
                window.mainMenuOpened = !window.mainMenuOpened
                window.dlgShutdown.visible = true
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
                window.pnlFileSelection.visible = false
                bindings.startFullAnalysis()
            }
        }

        Connections {
            target: window.btnStartStop

            function onClicked() {
                if(!bindings.analyzing) {
                    window.pnlFileSelection.visible = false
                } else {
                    window.pnlFileSelection.visible = true
                }

                bindings.startStopAnalysis()
            }
        }

        Connections {
            target: window.dlgSystemState

            function onButtonClicked() {
                window.dlgSystemState.visible = false
            }
        }

        Connections {
            target: window.dlgLog

            function onButtonClicked() {
                window.dlgLog.visible = false
            }
        }

        Connections {
            target: window.dlgRestart

            function onAccepted() {
                bindings.reset()
                window.dlgRestart.visible = false
                //window.pnlLoading.visible = true
                //window.pnlMessages.visible = true
            }

            function onRejected() {
                window.dlgRestart.visible = false
            }
        }

        Connections {
            target: window.dlgShutdown

            function onAccepted() {
                bindings.shutdown()
                window.dlgShutdown.visible = false
                //window.pnlMessages.visible = true
            }

            function onRejected() {
                window.dlgShutdown.visible = false
            }
        }

        Connections {
            target: window.dlgConnectStorage

            function onButtonClicked() {
                window.dlgConnectStorage.visible = false
            }
        }

        Connections {
            target: window.btnCopyFiles

            function onClicked() {
                window.pnlFilesCopy.visible = true
            }
        }

        Connections {
            target: window.btnLanguageEN

            function onClicked() {
                if(ApplicationController.language !== "")
                    ApplicationController.language = ""
                window.menuLanguagesOpened = !window.menuLanguagesOpened
            }
        }

        Connections {
            target: window.btnLanguageFR

            function onClicked() {
                if(ApplicationController.language !== "fr")
                    ApplicationController.language = "fr"
                window.menuLanguagesOpened = !window.menuLanguagesOpened
            }
        }

        Connections {
            target: window.btnShowViewer

            function onClicked() {
                console.debug("Switch to the viewer")
                bindings.switch_to_viewer()
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

        onSystemStateChanged: {
            if(bindings.systemState === Enums.TransferFinished) {
                window.pnlFilesCopy.visible = false
            } else if (bindings.systemState === Enums.SystemResetting) {
                window.pnlFilesCopy.visible = false
                window.pnlFileSelection.visible = false
                //window.pnlMessages.visible = true
            } else if (bindings.systemState === Enums.SystemReady) {
                window.dlgAnalyseWholeStorage.visible = true
            }
        }
    }

    Component.onCompleted: {
        // Verify whether a storage is connected
        if(ApplicationController.sourceReady) {
            window.dlgAnalyseWholeStorage.visible = true
        }

        if(DEVMODE) {
            //window.pnlFileSelection.visible = true
        }
    }

    onWidthChanged: {
        updateDimensions()
    }

    onHeightChanged: {
        updateDimensions()
    }

    /* Functions */
    function updateDimensions() {
        Environment.mainWidth = root.width
        Environment.mainHeight = root.height
    }
}

