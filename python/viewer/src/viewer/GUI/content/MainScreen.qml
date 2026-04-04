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
    title: "Saphir Viewer"    

    MainScreenUi {
        id: window

        anchors.fill: parent

        language: ApplicationController.language
        //backFilter.colorizationColor: bindings.systemStateColor
        imgBack.source: Environment.backgroundImage

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

        }

        Connections {
            target: window.dlgRestart

            function onAccepted() {
                bindings.reset()
                window.dlgRestart.visible = false
                window.pnlMessages.visible = true
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
                window.pnlMessages.visible = true
            }

            function onRejected() {
                window.dlgShutdown.visible = false
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

    Component.onCompleted: {
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

