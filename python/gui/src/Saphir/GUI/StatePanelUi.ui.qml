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
        text: ""
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
        text: ""
        level: PText.TextLevel.Paragraph
    }

    states: [
        State {
            name: "starting"

            PropertyChanges {
                target: lblState
                text: qsTr("Initialisation en cours...")
            }

            PropertyChanges {
                target: lblState
                text: qsTr("Veuillez patienter pendant le démarrage")
            }
        },
        State {
            name: "ready"

            PropertyChanges {
                target: lblState
                text: qsTr("Prêt pour analyse")
            }

            PropertyChanges {
                target: lblState
                text: qsTr("Veuillez sélectionner des fichiers")
            }
        },
        State {
            name: "waiting"

            PropertyChanges {
                target: lblState
                text: qsTr("En attente...")
            }

            PropertyChanges {
                target: lblState
                text: qsTr("Veuillez connecter un support")
            }
        },
        State {
            name: "running"
        }
    ]
}
