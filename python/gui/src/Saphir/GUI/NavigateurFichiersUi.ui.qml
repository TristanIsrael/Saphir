import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

Rectangle {
    id: root

    property bool input: false
    property bool diskReady: false
    property string diskName: qsTr("Sans nom")
    property var filesModel: diskReady ? (input ? inputFilesListModel : mockOutput) : undefined

    property alias btnAddWholeDisk: btnAddWholeDisk
    property alias btnAddFolder: btnAddFolder
    property alias tblView: tblView

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

        Rectangle {
            id: entete
            Layout.preferredWidth: parent.width
            implicitHeight: 50
            color: Constants.headingColor

            Icone {
                id: btnFolderUp
                anchors {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: 5
                }

                color: Constants.contrastColor
                text: "\ue5c4"
                visible: root.filesModel.currentFolder !== "/"
                pixelSize: 40

                Connections {
                    onClicked: {
                        root.filesModel.folder_up()
                        //root.tblView.contentY = 0
                        root.tblView.positionViewAtRow(0, TableView.Visible)
                    }
                }
            }

            RowLayout {
                anchors.centerIn: parent

                Icone {
                    id: icnUsb
                    text: root.input ? "\uf090" : "\uf09b"
                    color: Constants.contrastColor
                }

                PText {
                    id: lblDriveName
                    text: root.diskReady ? diskName : qsTr("Aucun disque branché")
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
                visible: root.input
                pixelSize: 40
            }           
        }

        TableView {
            id: tblView
            Layout.preferredWidth: parent.width
            Layout.preferredHeight: parent.height - entete.height - parent.spacing
                                    - (lytButtons.visible ? lytButtons.height : 0)
            rowSpacing: 0
            model: root.filesModel
            clip: true
            //selectionBehavior: TableView.SelectRows
            //selectionMode: TableView.SingleSelection
            //selectionModel: ItemSelectionModel{}

            delegate: Rectangle {
                id: dlg

                required property bool selected        
                required property var model        
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
                    text: filename
                    level: PText.TextLevel.Paragraph
                    color: progress === 100 ? Constants.contrastColor : Constants.textColor
                    elide: Text.ElideRight

                    anchors {
                        left: icn.right
                        leftMargin: 10
                        top: parent.top
                        bottom: parent.bottom
                        right: icnAdd.left
                        rightMargin: 5
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

                    Connections {
                        function onClicked() {                            
                            const fpath = filepath +(filepath === "/" ? "" : "/") +filename
                            ApplicationController.analyse_file(fpath)
                            dlg.model.inqueue = true
                        }
                    }
                }                

                MouseArea {
                    anchors {
                        left: parent.left
                        top: parent.top
                        bottom: parent.bottom
                        right: icnAdd.left
                    }

                    Connections {
                        function onClicked() {
                            dlg.model.selected = !dlg.model.selected
                        }
                    }
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

                Connections {
                    function onClicked() {                                                
                        var addToQueue = []

                        for(var row = 0 ; row < root.filesModel.rowCount() ; row++) {                            
                            const idx = root.filesModel.index(row, 0)
                            const type = root.filesModel.data(idx, root.roleFiletype)
                            //console.debug(row, idx, type)
                            if(type !== "file")
                                continue
                            const filename = root.filesModel.data(idx, root.roleFilename)
                            const filepath = root.filesModel.data(idx, root.roleFilepath)                            
                            const fpath = filepath+(filepath === "/" ? "" : filepath)+filename                            
                            
                            ApplicationController.analyse_file(fpath)       
                            addToQueue.push(idx)                                                 
                        }

                        for(var i = addToQueue.length-1 ; i >=0 ; i--) {
                            root.filesModel.setData(addToQueue[i], true, root.roleInqueue)
                        }
                    }
                }
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

    Connections {
        target: root.filesModel
        function onCurrentFolderChanged() {
            root.tblView.positionViewAtRow(0, TableView.Visible)
        }
    }

    /** Models */
    property var inputFilesListModel: ApplicationController.inputFilesListProxyModel
    property int roleFilename: root.filesModel.role("filename")
    property int roleFilepath: root.filesModel.role("filepath")
    property int roleFiletype: root.filesModel.role("type")
    property int roleInqueue: root.filesModel.role("inqueue")
    
    /** Développement */
    property var mockInput: MockInputFilesListModel {}
    property var mockOutput: MockOutputFilesListModel {}
}
