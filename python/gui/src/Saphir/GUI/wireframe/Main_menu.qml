import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main

    btnMenuThemes.visible: false

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
            y: parent.height -height

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
                    id: btnHelp
                    noborder: true
                    label: Constants.iconHelp
                    outlined: true
                }

                WfCircleButton {
                    id: btnSystemState
                    noborder: true
                    label: Constants.iconSystemState
                }

                WfCircleButton {
                    id: btnLog
                    noborder: true
                    label: Constants.iconLog
                }

                WfCircleButton {
                    id: btnRestart
                    noborder: true
                    label: Constants.iconRestart
                }

                WfCircleButton {
                    id: btnShutdown
                    noborder: true
                    label: Constants.iconShutdown
                }
            }
        }
    }
}
