import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"


Rectangle {
    id: rootModalFileList
    color: "transparent"

    property int maxFoldersDisplayed: 6
    property int maxFilesDisplayed: 10
    property int idFolderSelected: -1
    property int idParentFolder: -1
    property bool selectionMode: Constants.isFileSelectionMode

    function findItem(searchId)
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
            if (/*item.type === "file" &&*/item.parent === idFolderSelected)
            {
                //Tester de voir si on append direct item ?
                fileListView.append({id: i, type: item.type, name: item.name, selected: item.selected, backId: item.backId})
            }
        }
    }

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
            return "#445060"
        }
    }

    Image {
        id: background
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "Modale.svg")
        width: parent.width
        height: parent.height
        fillMode: Image.Stretch
        anchors.fill: parent
    }

    Image {
        id: returnButton
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FermerModale.svg")
        height: parent.height * 0.12
        width: parent.width * 0.075
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: (parent.width * 0.02) + (width * 0.5)
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

    RowLayout {
        anchors.fill: modalContentContainer
        Rectangle {
            Layout.preferredWidth: 30
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: 'transparent'
            ListView {
                clip: true
                id: folderListView
                Layout.alignment: Qt.AlignCenter
                width: parent.width
                height: parent.height
                model: Constants.fileList

                delegate : Rectangle {
                    width: parent.width*0.95
                    height: model.type === "folder" ? parent.parent.height * (1.0/maxFoldersDisplayed) : 0
                    visible: model.type === "folder"
                    color: "transparent"
                    Image {
                        source: idFolderSelected === model.backId ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaireActive.svg")
                                                                  : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaireActif.svg")
                        width:parent.width
                        height:parent.height
                        anchors.centerIn: parent
                        fillMode: Image.PreserveAspectFit
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                idFolderSelected = model.backId
                                updateFileList()
                            }
                        }
                    }
                    Label {
                        height: parent.height * 0.5
                        width: parent.width * 0.5
                        anchors.centerIn: parent
                        text: model.name
                        color: getFolderTextColor()
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Label.ElideRight
                    }
                }
            }

        }

        Rectangle {
            Layout.preferredWidth: 70
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            ListView
            {
                clip:true
                id: listView
                width: parent.width
                height: parent.height
                model: ListModel { id: fileListView }

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
                    width: parent.width*0.95
                    height: parent.parent.height*(1.0/maxFilesDisplayed)
                    Layout.minimumHeight: 30
                    Item {
                        Layout.preferredWidth: 10
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;

                        Image {
                            width:parent.width
                            height:parent.height
                            anchors.verticalCenter: parent.verticalCenter
                            source: model.type === "file" ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "FichierActif.svg")
                                                          : model.type === "folder" && model.backId !== idParentFolder ? Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaire.svg")
                                                                                                                       : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireParent.svg")
                            fillMode: Image.PreserveAspectFit

                            MouseArea {
                                anchors.fill: parent
                                enabled: model.type === "folder"
                                onClicked: {
                                    idFolderSelected = model.backId
                                    updateFileList()
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                enabled: model.type === "folder-parent"
                                onClicked: {
                                    Constants.enterFolder(model.backId)
                                }
                            }
                        }
                    }
                    Label
                    {
                        clip:true
                        color: model.selected ? Constants.colorBlue : Constants.colorText
                        Layout.preferredWidth: 90
                        text: (model.backId === idParentFolder ? "Dossier parent - " : "") + model.name
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        verticalAlignment: Text.AlignVCenter
                        elide: Label.ElideRight
                    }
                    CheckBox
                    {
                        id: checkBox
                        visible: model.type === "file" && selectionMode
                        Layout.preferredWidth: 15
                        Layout.fillWidth: true;
                        Layout.fillHeight: true
                        checked: model.selected
                        onCheckedChanged: {
                            //Changement dans la liste actuelle
                            model.selected = checked
                            //Changement dans la liste originelle
                            //Constants.fileList.get(model.id).selected = checked
                            for(let i = 0; i < Constants.fileList.count; i++)
                            {
                                var item = Constants.fileList.get(i)
                                if (item.backId === model.backId)
                                    item.selected = checked
                            }

                            if(checked)
                            {
                                Constants.analyseFile(model.type,
                                                          model.name,
                                                          model.selected,
                                                          model.status,
                                                          0.0 ,
                                                          model.backId)
                            }
                        }
                        contentItem: Image {
                            anchors.verticalCenter: parent.verticalCenter
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherActive.svg")
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            Layout.fillHeight: true
                        }
                        indicator: Image {
                            visible: parent.checked
                            anchors.verticalCenter: parent.verticalCenter
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CocheActif.svg")
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            Layout.fillHeight: true
                            width: parent.width*0.5
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
