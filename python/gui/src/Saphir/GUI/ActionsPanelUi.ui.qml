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
    property alias btnStartTransfer: btnStartTransfer

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
            id: btnStartTransfer
            anchors {
                right: parent.right
                rightMargin: 24
                verticalCenter: parent.verticalCenter
            }
            
            pixelSize: parent.height * 0.9
            enabled: ApplicationController.cleanFilesCount > 0 && ApplicationController.targetReady
            text: "\ue255"
        }

        Icone {
            id: btnStartPauseResumeAnalysis
            anchors {
                right: btnStartTransfer.left
                rightMargin: 24
                verticalCenter: parent.verticalCenter
            }
            
            pixelSize: parent.height * 0.9
            enabled: ApplicationController.queueSize > 0 && ApplicationController.analysisReady
            text: ApplicationController.systemState === Enums.SystemState.SystemReady ? "\ue039" : ApplicationController.systemState === Enums.SystemState.SystemRunning ? "\ue036" : "\ueb8b"
        }

        Icone {
            id: btnStartOver
            anchors {
                right: btnStartPauseResumeAnalysis.left
                rightMargin: 24
                verticalCenter: parent.verticalCenter
            }
            
            pixelSize: parent.height * 0.9
            enabled: false
            text: "\uf053"
        }

        Icone {
            id: btnShutdown
            anchors {
                left: parent.left
                leftMargin: 24
                verticalCenter: parent.verticalCenter
            }
            
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
                top: parent.top
                bottom: parent.bottom
                left: btnHelp.right
                right: btnStartOver.left
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
