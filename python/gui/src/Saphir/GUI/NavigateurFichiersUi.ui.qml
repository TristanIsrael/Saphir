import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property bool input: false
    property bool diskReady: false
    property string diskName: qsTr("Sans nom")
    property var filesModel: diskReady ? (input ? mockInput : mockOutput) : undefined

    property alias btnAddWholeDisk: btnAddWholeDisk
    property alias btnAddFolder: btnAddFolder

    implicitWidth: 500
    implicitHeight: 600

    border {
        width: 0
        color: "transparent"
    }

    ColumnLayout {
        id: colLyt

        anchors {
            fill: parent
            bottomMargin: 10
        }

        //spacing: 0
        Rectangle {
            id: entete
            Layout.preferredWidth: parent.width
            implicitHeight: 50
            color: Constants.headingColor

            RowLayout {
                anchors.centerIn: parent

                Icone {
                    id: icnUsb
                    text: input ? "\uf090" : "\uf09b"
                    color: Constants.contrastColor
                }

                PText {
                    id: lblDriveName
                    text: diskReady ? diskName : qsTr("Aucun disque branché")
                    color: Constants.contrastColor
                    font.capitalization: Font.SmallCaps
                }
            }

            Icone {
                id: btnAddWholeDisk
                anchors {
                    verticalCenter: parent.verticalCenter
                    right: parent.right
                    rightMargin: 5
                }

                color: Constants.contrastColor
                text: "\ue03b"
                visible: input
                pixelSize: 40
            }
        }

        TableView {
            id: tblView
            Layout.preferredWidth: parent.width
            Layout.preferredHeight: parent.height - entete.height - parent.spacing
                                    - (lytButtons.visible ? lytButtons.height : 0)
            rowSpacing: 0
            model: filesModel

            delegate: Rectangle {
                implicitWidth: tblView.width
                implicitHeight: 40

                //Un fichier analysé ne peut pas être sélectionné
                color: progress === 100 ? (infected ? Constants.alertColor : Constants.successColor) : (selected ? Constants.selectionColor : "transparent")

                Icone {
                    id: icn
                    anchors {
                        left: parent.left
                        leftMargin: 5
                        verticalCenter: parent.verticalCenter
                    }

                    text: type === "folder" ? "\ue2c7" : type === "file" ? "\ue24d" : "\ue316"
                    color: progress === 100 ? Constants.contrastColor : Constants.buttonColor
                }

                PText {
                    text: type === "up" ? "Remonter" : filename
                    level: type === "up" ? PText.TextLevel.Indice : PText.TextLevel.Paragraph
                    font.italic: type === "up" ? true : false
                    color: progress === 100 ? Constants.contrastColor : Constants.textColor

                    anchors {
                        left: icn.right
                        leftMargin: 10
                        top: parent.top
                        bottom: parent.bottom
                    }
                    verticalAlignment: Text.AlignVCenter
                }

                Icone {
                    id: icnAdd
                    text: "\ue03b"
                    color: Constants.intermediateColor
                    anchors {
                        right: parent.right
                        rightMargin: 5
                        verticalCenter: parent.verticalCenter
                    }
                    visible: selected && input
                    pixelSize: 40
                }
            }
        }

        RowLayout {
            id: lytButtons
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            spacing: height
            visible: input && diskReady

            BoutonAction {
                id: btnAddFolder
                text: qsTr("Tout le dossier")
                icone: "\ue03b"
            }
        }
    }

    PText {
        id: lblAskForDevice

        anchors {
            left: parent.left
            right: parent.right
            margins: 10
            centerIn: parent
        }

        level: PText.TextLevel.H3
        text: qsTr("Veuillez connecter un disque")
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        visible: !diskReady
    }

    /** Développement */
    property var mockInput: MockInputFilesListModel {}
    property var mockOutput: MockOutputFilesListModel {}
}
