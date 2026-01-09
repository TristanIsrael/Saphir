import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Components
import Qt5Compat.GraphicalEffects

Window {
    id: root

    property bool ready: false
    property bool running: false
    property string theme: "light"

    property alias btnMenuThemes: btnMenuThemes
    property alias btnMainMenu: btnMainMenu

    width: Environment.mainWidth
    height: Environment.mainHeight

    WfPanel {
        anchors.fill: parent

        WfText {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 20
            text: "SAPHIR"
            font.pixelSize: 24
        }

        WfText {
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.top: parent.top
            anchors.topMargin: 20
            text: "09:21:34Z"
        }

        WfText {
            text: "Capability: RESTRICTED"

            anchors {
                left: parent.left
                leftMargin: 200
                top: parent.top
                topMargin: 20
            }

            font.italic: true
        }

        // Upper right icons
        RowLayout {
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.top: parent.top
            anchors.topMargin: 16

            Text {
                font.family: "Material Icons Outlined"
                font.pixelSize: 28
                text: "\ue63c"
            }

            WfBattery { }
        }

        // Lower right icons
        WfCircleButton {
            id: btnStartPause

            anchors {
                right: parent.right
                rightMargin: 10
                bottom: parent.bottom
                bottomMargin: 10
            }

            label: root.running ? Constants.iconPause : Constants.iconStart
            outlined: false            
        }

        // Lower right icons    
        Popup {
            id: btnMenuThemes
            visible: true
            popupType: Popup.Item
            closePolicy: Popup.NoAutoClose

            x: 0
            y: parent.height - height - btnMainMenu.height - 5

            background: Rectangle {
                color: "transparent"
            }

            WfCircleButton {
                label: root.theme === "light" ? Constants.iconThemeLight : root.theme === "dark" ? Constants.iconThemeDark : Constants.iconThemeLowVisibility
                outlined: false
                noborder: true
            }
        }

        Popup {
            id: btnMainMenu
            visible: true
            popupType: Popup.Item
            closePolicy: Popup.NoAutoClose

            x: 0
            y: parent.height - height - 5

            background: Rectangle {
                color: "transparent"
            }

            WfCircleButton {
                label: Constants.iconMenu
            }
        }
    }
}
