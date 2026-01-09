import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main

    WfPanel {
        id: pnl

        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            margins: height/10
        }

        WfText {
            anchors.centerIn: parent
            text: "Display content"
        }

        Popup {
            id: pnlMenu

            visible: true
            x: -80
            y: parent.height -height -85

            width: lyt.width + 20
            height: lyt.height + 20

            background: Rectangle {
                color: "#33444444"
                radius: 10
            }

            ColumnLayout {
                id: lyt

                spacing: 10

                anchors.horizontalCenter: parent.horizontalCenter                

                WfCircleButton {
                    id: btnThemeLight
                    noborder: true
                    label: Constants.iconThemeLight
                    outlined: true
                }

                WfCircleButton {
                    id: btnThemeDark
                    noborder: true
                    label: Constants.iconThemeDark
                }

                WfCircleButton {
                    id: btnThemeLowVisibility
                    noborder: true
                    label: Constants.iconThemeLowVisibility
                }                
            }
        }
    }
}
