import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

Rectangle {
    id: root

    property alias btnHelp: btnHelp
    property alias btnShutdown: btnShutdown
    property alias btnStartOver: btnStartOver
    property alias btnStartPauseResumeAnalysis: btnStartPauseResumeAnalysis
    property alias pnlState: pnlState

    height: implicitHeight
    width: implicitWidth
    implicitWidth: 1900
    implicitHeight: 190
    color: Constants.contrastColor
    //state: ""

    Item {
        anchors {
            fill: parent
        }

        Icone {
            anchors {
                right: parent.right
                rightMargin: 24
                verticalCenter: parent.verticalCenter
            }

            id: btnStartPauseResumeAnalysis
            pixelSize: parent.height * 0.9
            enabled: false
            text: ApplicationController.systemState === Enums.SystemState.SystemReady ? "\ue039" : ApplicationController.systemState === Enums.SystemState.SystemRunning ? "\ue036" : "\ueb8b"
        }

        Icone {
            anchors {
                right: btnStartPauseResumeAnalysis.left
                rightMargin: 24
                verticalCenter: parent.verticalCenter
            }

            id: btnStartOver
            pixelSize: parent.height * 0.9
            enabled: false
            text: "\uf053"
        }

        Icone {
            anchors {
                left: parent.left
                leftMargin: 24
                verticalCenter: parent.verticalCenter
            }

            id: btnShutdown
            pixelSize: parent.height * 0.9
            enabled: true
            text: "\ue646" //"\ue9b2"
        }

        Icone {
            id: btnHelp
            anchors {
                left: btnShutdown.right
                leftMargin: 24
                verticalCenter: parent.verticalCenter
            }

            pixelSize: parent.height * 0.9
            enabled: true
            text: "\ue8fd"
        }

        StatePanel {
            id: pnlState
            anchors {
                verticalCenter: parent.verticalCenter
                horizontalCenter: parent.horizontalCenter
            }            
        }
    }

    /*states: [
        State {
            name: "starting"
        },
        State {
            name: "ready"
        },
        State {
            name: "running"
        }
    ]*/
}
