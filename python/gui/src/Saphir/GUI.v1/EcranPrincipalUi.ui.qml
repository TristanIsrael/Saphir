import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import net.alefbet 

FondEcranUi {
    id: root

    property alias msgBox: msgBox

    RowLayout {
        id: rLyt
        anchors {
            top: parent.top
            topMargin: parent.headerHeight + 10
            left: parent.left
            right: parent.right
            bottom: pnlEtatActions.top
            margins: 10
        }
        spacing: 10

        NavigateurFichiers {
            id: pnlNavigatorInput

            input: true
            Layout.preferredHeight: parent.height
            Layout.preferredWidth: (parent.width - rLyt.spacing * 2) / 3
        }

        ResultsListPanel {
            id: pnlResultsList

            Layout.preferredHeight: parent.height
            Layout.preferredWidth: (parent.width - rLyt.spacing * 2) / 3
        }

        NavigateurFichiers {
            id: pnlNavigatorOutput

            input: false
            Layout.preferredHeight: parent.height
            Layout.preferredWidth: (parent.width - rLyt.spacing * 2) / 3
        }
    }

    ActionsPanel {
        id: pnlEtatActions

        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        height: parent.height / 10
    }

    HelpPanelUi {
        id: hlpIN
        x: pnlNavigatorInput.x + (pnlNavigatorInput.width - width) / 2
        y: pnlNavigatorInput.height / 2
        visible: pnlEtatActions.btnHelp.pressed
        title: qsTr("Support source")
        comment: qsTr("Connectez un support USB afin d'afficher son contenu et de choisir les fichiers à analyser.")
    }

    HelpPanelUi {
        id: hlpOUT
        x: pnlNavigatorOutput.x + ((pnlNavigatorOutput.width - width) / 2)
        y: pnlNavigatorOutput.height / 2
        visible: pnlEtatActions.btnHelp.pressed
        title: qsTr("Support cible")
        comment: qsTr("Connectez un support USB afin d'afficher son contenu et de choisir les fichiers à analyser.")
    }

    HelpPanelUi {
        id: hlpResults
        x: pnlResultsList.x + ((pnlResultsList.width - width) / 2)
        y: pnlResultsList.height / 2
        visible: pnlEtatActions.btnHelp.pressed
        title: qsTr("Analyse")
        comment: qsTr("Les fichiers en cours d'analyse et les résultats sont affichés ici.")
    }

    HelpPanelUi {
        id: hlpShutdown
        x: pnlEtatActions.x
        y: pnlEtatActions.y - height * 0.7
        width: pnlEtatActions.btnShutdown.width * 2
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Arrêter le système.")
    }

    HelpPanelUi {
        id: hlpBtnAddFolder
        x: pnlNavigatorInput.x + pnlNavigatorInput.width / 2
        y: pnlNavigatorInput.y + pnlNavigatorInput.height - height
        width: pnlNavigatorInput.btnAddFolder.width
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Sélectionner tout le dossier courant.")
    }

    HelpPanelUi {
        id: hlpBtnAddDisk
        x: pnlNavigatorInput.x + pnlNavigatorInput.width * 0.8
        y: pnlNavigatorInput.y + height + 25
        width: pnlNavigatorInput.btnAddFolder.width
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Sélectionner tout le disque.")
    }

    HelpPanelUi {
        id: hlpResultsCount
        x: pnlResultsList.x + (pnlResultsList.width - width) / 2
        y: pnlResultsList.y + pnlResultsList.height - height - 10
        width: pnlNavigatorInput.btnAddFolder.width
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Résultats de l'analyse.")
    }

    HelpPanelUi {
        id: hlpStartOver
        x: pnlEtatActions.btnStartOver.x - width
        y: pnlEtatActions.y + pnlEtatActions.btnStartOver.y
        width: pnlNavigatorInput.btnAddFolder.width
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Réinitialiser le système.")
    }

    HelpPanelUi {
        id: hlpPause
        x: parent.width - width
        y: pnlEtatActions.y + pnlEtatActions.btnStartPauseResumeAnalysis.y - height
        width: pnlNavigatorInput.btnAddFolder.width
        visible: pnlEtatActions.btnHelp.pressed
        comment: qsTr("Mettre en pause l'analyse.")
    }

    MessageBox {
        id: msgBox        

        anchors {
            fill: parent
        }
        visible: false
    }

}
