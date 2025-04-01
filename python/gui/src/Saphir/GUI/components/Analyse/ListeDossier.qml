import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Rectangle {
    color: "transparent"

    property bool selectionMode: Constants.isFileSelectionMode
    property int itemDisplayed: 10
    property ListModel _fileList
    property string idFolderSelected: ApplicationController.idCurrentFolder
    property int currentParentFolder

    Component.onCompleted: {
        updateParentFolder()
    }

    Connections {
        target: Constants
        onUpdateCurrentPath: {
            Constants.currentDirectory = newPath
            Constants.currentDirectoryId = idFolder
            updateParentFolder()
        }

        onClearFileList: {
            Constants.fileList.clear()
        }
    }

    function updateParentFolder()
    {
        return 

        for (let i = 0; i < Constants.fileList.count; i++)
        {
            if (Constants.fileList.get(i).backId === Constants.currentDirectoryId)
            {
                currentParentFolder = Constants.fileList.get(i).parent
                noParentHandler()
            }
        }
    }

    function noParentHandler()
    {
        if(currentParentFolder < 0)
            return

        for (let i = 0; i < Constants.fileList.count; i++)
        {
            if (Constants.fileList.get(i).backId === currentParentFolder)
                return
        }
        Constants.fileList.append({ backId: currentParentFolder,
                                        type: "folder",
                                        name: "parent",
                                        selected: false,
                                        status: Constants.FileState.NOT_ANALYSED,
                                        parent: -1})
    }

    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportEntree.svg")
    }

    ColumnLayout
    {
        anchors {
            fill: parent
            topMargin: parent.height*0.01
            bottomMargin: parent.height*0.1
            leftMargin:parent.width*0.03
            rightMargin: parent.width*0.03
        }

        clip: true
        spacing: 20

        Item {
            Layout.preferredHeight: 5
        }

        /* Fil d'Ariane */
        Label
        {
            color: Constants.colorText
            Layout.fillWidth: true
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            text: ApplicationController.currentFolder
            font.pixelSize: height * 1.0
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideLeft
        }

        /** Retour au dossier parent */
        RowLayout {
            id: lblParentFolder
            visible: idFolderSelected !== "/"

            Layout.preferredWidth: parent.width
            Layout.preferredHeight: 10
            spacing: 10

            Image {
                Layout.preferredWidth: 25
                anchors.verticalCenter: parent.verticalCenter
                source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireParent.svg")
                fillMode: Image.PreserveAspectFit                    

                MouseArea {
                    anchors.fill: parent
                    //enabled: type === "folder-parent"
                    onClicked: {
                        //idParentFolder = backId
                        //ApplicationController.go_to_folder(filepath)
                        ApplicationController.go_to_parent_folder()
                        //Constants.enterFolder(backId)
                    }
                }
            }
            
            Label
            {                                        
                clip: true
                color: Constants.colorText
                //Layout.preferredWidth: 90                        
                text: "Dossier parent"
                Layout.fillHeight: true
                Layout.fillWidth: true
                //font.pixelSize: height*0.6
                font.pointSize: 24
                verticalAlignment: Text.AlignLeft
                elide: Label.ElideRight

                MouseArea {
                    anchors.fill: parent
                    //enabled: type === "folder"
                    onClicked: {
                        ApplicationController.go_to_parent_folder()
                    }
                }
            }                
        } 

        ListView
        {
            id: listView
            clip: true

            Layout.preferredHeight: 95
            Layout.fillWidth: true
            Layout.fillHeight: true

            model: Constants.fileList
            spacing: 20

            ScrollBar.vertical: ScrollBar
            {
                policy: parent.contentHeight > parent.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                width:parent.width*0.03
                background: Rectangle {
                    implicitWidth: parent.parent.width*0.01
                    color: "#00000000"  // Couleur du fond de la scrollbar
                    radius: 6
                    border.color: Constants.colorText
                }

                contentItem: Rectangle {
                    implicitWidth: parent.parent.width*0.01
                    color: Constants.colorText  // Couleur de la barre de défilement
                    radius: 6
                }
            }

            delegate: RowLayout
            {
                height: visible ? 25 : 0                    
                width: selectionMode ? listView.width *0.92 : listView.width
                spacing: 10
                
                Image {
                    Layout.preferredWidth: parent.height 
                    Layout.preferredHeight: parent.height                        

                    //anchors.verticalCenter: parent.verticalCenter
                    /*source: type === "file" ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FichierActif.svg")
                                                    : type === "folder" && backId !== idParentFolder ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaire.svg")
                                                                                                                : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireParent.svg")*/
                    source: type === "file" ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FichierActif.svg")
                                            : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaire.svg")                                                                           
                    fillMode: Image.PreserveAspectFit
                    
                    MouseArea {
                        anchors.fill: parent
                        enabled: type === "folder"
                        onClicked: {
                            idFolderSelected = backId
                            ApplicationController.go_to_folder(filepath)
                        }
                    }
                }          

                Label
                {
                    clip: true
                    color: model.selected ? Constants.colorBlue : Constants.colorText
                    text: filename                        
                    font.pointSize: 24
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignLeft
                    elide: Label.ElideRight
                    Layout.fillWidth: true

                    MouseArea {
                        anchors.fill: parent
                        enabled: type === "folder"
                        onClicked: {
                            idFolderSelected = backId
                            ApplicationController.go_to_folder(filepath)
                            //updateFileList()
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                CheckBox {
                    id: checkBox
                    //visible: type === "file" //&& selectionMode
                    visible: selectionMode
                    Layout.preferredHeight: parent.height
                    Layout.preferredWidth: parent.height
                    checked: selected

                    background: Item {}

                    contentItem: Image {
                        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherActive.svg")
                        anchors.centerIn: parent
                        fillMode: Image.PreserveAspectFit
                        anchors.fill: parent
                    }

                    indicator: Image {
                        visible: parent.checked
                        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CocheActif.svg")
                        width: parent.width*0.6
                        height: width
                        fillMode: Image.PreserveAspectFit
                        anchors.centerIn: parent
                    }

                    onCheckedChanged: function() {
                        if(checked) {
                            Constants.addToAnalyse(
                                type,
                                filename,
                                selected,
                                status,
                                0.0,
                                backId)
                        } else {
                            Constants.removeFromAnalyse(
                                type,
                                filename,
                                selected,
                                status,
                                0.0,
                                backId)
                        }
                    }
                }                    
            }

            Label
            {
                id: usbKeyLabel
                visible: Constants.fileList.count === 0
                color: Constants.colorText
                anchors.fill: parent
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: "Veuillez insérer une clé USB"
                font.pixelSize: width * 0.07
            }
        }
    }
}
