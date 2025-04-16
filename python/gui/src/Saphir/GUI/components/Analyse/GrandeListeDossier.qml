import QtQuick
import QtQuick.Controls
//import QtQuick.Controls.Basic
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Rectangle {
    id: rootModalFileList
    color: "transparent"

    property int maxFoldersDisplayed: 6
    property int maxFilesDisplayed: 10
    property string idFolderSelected: ApplicationController.idCurrentFolder
    //property string idParentFolder: "/"
    property bool selectionMode: Constants.isFileSelectionMode

    /*function findItem(searchId)
    {
        for (let i = 0; i < Constants.fileList.count; i++)
        {
            if (Constants.fileList.get(i).backId === searchId)
                return Constants.fileList.get(i)
        }
        return undefined
    }

    function updateFileList() {        
        fileListView.clear()

        //Recherche du parent
        var currentFolder = findItem(idFolderSelected)
        idParentFolder = currentFolder.parent
        if (currentFolder.parent >= 0)
        {
            var parentFolder = findItem(currentFolder.parent)
            if(parentFolder !== undefined)
            {
                fileListView.append({type: parentFolder.type, name: parentFolder.name, selected: parentFolder.selected,  backId: idParentFolder})
            }
            else
            {
                fileListView.append({type: "folder-parent", name: "parent", selected: false,  backId: currentFolder.parent})
            }
        }

        //fileListView.append({id: i, type: item.type, name: item.name, selected: item.selected})
        for (let i = 0; i < Constants.fileList.count; i++)
        {
            var item = Constants.fileList.get(i)
            if (item.parent === idFolderSelected)
            {
                //Tester de voir si on append direct item ?
                fileListView.append({id: i, type: item.type, name: item.name, selected: item.selected, backId: item.backId})
            }
        }
    }*/

    function getFolderTextColor()
    {
        let mode = Constants.currentColorMode
        switch(mode)
        {
        case Constants.ColorMode.STEALTH:
            return "#1E1E1E"
        case  Constants.ColorMode.LIGHT:
            return "#FFFFFF"
        default:
            return "#fff"
            //return "#445060"
        }
    }

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath  + "Modale.svg")
        width: parent.width
        height: parent.height
        fillMode: Image.Stretch
        anchors.fill: parent
    }

    Image {
        id: returnButton
        source: Qt.resolvedUrl(Constants.colorModePath  + "FermerModale.svg")
        height: parent.height * 0.12
        width: parent.width * 0.075
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: (parent.width * 0.02) + (width * 0.5)
        fillMode: Image.PreserveAspectFit
        MouseArea {
            anchors.fill: parent
            onClicked: rootModalFileList.visible = !rootModalFileList.visible
        }
    }

    Rectangle {
        id: modalContentContainer
        anchors.centerIn: parent
        width: parent.width * 0.96
        height: parent.height * 0.85
        anchors.verticalCenterOffset: parent.height * -0.05
        color: "transparent"
    }    

    /** Fil d'Ariane */
    Label {
        id: lbLFilAriane
        width: modalContentContainer.width
        height: 20

        anchors {       
            top: modalContentContainer.top
            topMargin: 10
            left: modalContentContainer.left
            right: modalContentContainer.right
        }
        
        horizontalAlignment: Text.AlignHCenter
        font.pointSize: 18
        text: ApplicationController.currentFolder
    }    

    RowLayout {        

        anchors {
            top: lbLFilAriane.bottom
            left: modalContentContainer.left             
            right: modalContentContainer.right
            bottom: modalContentContainer.bottom
            margins: 10
        }        

        /* Liste des dossiers */
        /*Rectangle {
            Layout.preferredWidth: parent.width/2
            Layout.fillHeight: true
            //Layout.fillWidth: true
            color: 'transparent'
            visible: false

            ListView {
                clip: true
                id: folderListView
                Layout.alignment: Qt.AlignCenter
                anchors.fill: parent
                model: Constants.fileList

                delegate : RowLayout {
                    //width: parent.width
                    Layout.fillWidth: true
                    height: type === "folder" ? parent.parent.height * (1.0/maxFoldersDisplayed) : 0
                    visible: type === "folder"
                    //color: "transparent"

                    Image {
                        source: idFolderSelected === backId ? Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaireActive.svg")
                                                                  : Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaireActif.svg")
                        width:height
                        height:parent.height
                        //anchors.centerIn: parent
                        //fillMode: Image.PreserveAspectFit
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                idFolderSelected = backId
                                ApplicationController.go_to_folder(filepath)
                                //updateFileList()
                            }
                        }
                    }
                    
                    Label {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: filename
                        color: getFolderTextColor()
                        //font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        font.pointSize: 24
                        font.bold: true
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter
                        elide: Label.ElideRight
                    }
                }
            }

        }*/

        /** Liste des fichiers */
        Rectangle {
            //Layout.preferredWidth: 70
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"          

            /** Retour au dossier parent */
            RowLayout {
                id: lblParentFolder
                visible: idFolderSelected !== "/"

                anchors {
                    top: parent.top
                    left: parent.left
                    //right: parent.right
                }        

                Image {
                    Layout.preferredWidth: 50
                    anchors.verticalCenter: parent.verticalCenter
                    source: Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireParent.svg")
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
                    verticalAlignment: Text.AlignVCenter
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
                anchors {
                    top: lblParentFolder.bottom
                    topMargin: 20
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }
                clip:true
                model: Constants.fileList
                spacing: 20
                //model: ListModel { id: fileListView }

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
                    height: visible ? 50 : 0                    
                    width: listView.width *0.95
                    spacing: 10
                    
                    Image {
                        Layout.preferredWidth: parent.height 
                        Layout.preferredHeight: parent.height                        

                        //anchors.verticalCenter: parent.verticalCenter
                        /*source: type === "file" ? Qt.resolvedUrl(Constants.colorModePath  + "FichierActif.svg")
                                                        : type === "folder" && backId !== idParentFolder ? Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaire.svg")
                                                                                                                    : Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireParent.svg")*/
                        source: type === "file" ? Qt.resolvedUrl(Constants.colorModePath  + "FichierActif.svg")
                                                : Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaire.svg")                                                                           
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
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: parent.height
                        checked: selected

                        background: Item {}

                        contentItem: Image {
                            source: Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherActive.svg")
                            anchors.centerIn: parent
                            fillMode: Image.PreserveAspectFit
                            anchors.fill: parent
                        }

                        indicator: Image {
                            visible: parent.checked
                            source: Qt.resolvedUrl(Constants.colorModePath  + "CocheActif.svg")
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
}
