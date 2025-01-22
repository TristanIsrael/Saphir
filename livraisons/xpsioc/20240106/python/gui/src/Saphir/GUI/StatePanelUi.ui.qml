import QtQuick
import QtQuick.Controls

Item {
    id: root

    /*PText {
        id: lblState
        anchors {
            top: parent.top
            topMargin: 5
            left: parent.left
            right: parent.right
        }

        horizontalAlignment: Qt.AlignHCenter
        text: qsTr("Getting ready")
        level: PText.TextLevel.H3
    }*/

    PText {
        id: lblInformation
        anchors {
            fill: parent
            margins: 5
        }
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        text: qsTr("The system is starting")
        level: PText.TextLevel.H3
    }

    states: [
        State {
            name: "waiting"

            /*PropertyChanges {
                target: lblState
                text: qsTr("En attente")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("Please connect a drive")
            }
        },
        State {
            name: "starting"

            /*PropertyChanges {
                target: lblState
                text: qsTr("Démarrage")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("The system is starting")
            }
        },
        State {
            name: "waiting_for_user"

            /*PropertyChanges {
                target: lblState
                text: qsTr("En attente")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("Waiting for user action")
            }
        },
        State {
            name: "ready"

            /*PropertyChanges {
                target: lblState
                text: qsTr("Prêt")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("The system is ready")
            }
        },        
        State {
            name: "running"

            /*PropertyChanges {
                target: lblState
                text: qsTr("Tâche en cours")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("Task running...")
            }
        },
        State {
            name: "getting_files_list"

            /*PropertyChanges {
                target: lblState
                text: qsTr("Lecture")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("Getting files list")
            }
        },
        State {
            name: "analysis_running"

            /*PropertyChanges {
                target: lblState
                text: qsTr("Analyse")
            }*/

            PropertyChanges {
                target: lblInformation
                text: qsTr("Analysis running...")
            }
        }
    ]
}
