import QtQuick
import QtQuick.Controls

Item {
    id: root

    PText {
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
    }

    PText {
        id: lblInformation
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            bottomMargin: 5
        }
        horizontalAlignment: Qt.AlignHCenter
        text: qsTr("The system is starting")
        level: PText.TextLevel.Paragraph
    }

    states: [
        State {
            name: "waiting"

            PropertyChanges {
                target: lblState
                text: qsTr("En attente")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Veuillez connecter un support")
            }
        },
        State {
            name: "starting"

            PropertyChanges {
                target: lblState
                text: qsTr("Démarrage")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Le système est en train de démarrer...")
            }
        },
        State {
            name: "waiting_for_user"

            PropertyChanges {
                target: lblState
                text: qsTr("En attente")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("En attente d'une action utilisateur...")
            }
        },
        State {
            name: "ready"

            PropertyChanges {
                target: lblState
                text: qsTr("Prêt")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Le système est prêt")
            }
        },        
        State {
            name: "running"

            PropertyChanges {
                target: lblState
                text: qsTr("Tâche en cours")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Une tâche est en cours...")
            }
        },
        State {
            name: "getting_files_list"

            PropertyChanges {
                target: lblState
                text: qsTr("Lecture")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Récupération de la liste des fichiers...")
            }
        },
        State {
            name: "analysis_running"

            PropertyChanges {
                target: lblState
                text: qsTr("Analyse")
            }

            PropertyChanges {
                target: lblInformation
                text: qsTr("Une analyse des fichiers est en cours...")
            }
        }
    ]
}
