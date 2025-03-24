import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"


Rectangle {
    color: "transparent"

    property bool selectionMode: Constants.isFileSelectionMode
    property int itemDisplayed: 10
    property ListModel _fileList
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
        anchors.fill: parent
        anchors.topMargin: parent.height*0.01
        anchors.bottomMargin: parent.height*0.1
        anchors.leftMargin:parent.width*0.03
        anchors.rightMargin: parent.width*0.03
        Label
        {
            color: Constants.colorText
            Layout.fillWidth: true
            Layout.preferredHeight: 5
            Layout.fillHeight: true
            text: Constants.currentDirectory
            font.pixelSize: height * 1.0
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }


        ListView
        {
            clip:true
            id:listView
            Layout.preferredHeight: 95
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: _fileList
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
                visible: Constants.currentDirectoryId !== model.backId
                width: parent.width*0.95
                height: Constants.currentDirectoryId !== model.backId ? parent.parent.height*(1.0/itemDisplayed) : 0
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
                                                      : Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "IconeRepertoireUnitaire.svg")
                        fillMode: Image.PreserveAspectFit

                        MouseArea {
                            anchors.fill: parent
                            enabled: model.type === "folder"
                            onClicked: {
                                //Envoi du signal pour rentrer dans le dossier
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
                    text: currentParentFolder === model.backId ? ("Dossier parent - " + model.name) : model.name
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
                        model.selected = checked
                        if (checked)
                        {
                            Constants.analyseFile(model.type,
                                                      model.name,
                                                      model.selected,
                                                      model.status,
                                                      0.0,
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
                visible: parent.contentHeight === 0
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
