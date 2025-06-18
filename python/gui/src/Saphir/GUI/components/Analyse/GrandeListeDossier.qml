import QtQuick
import QtQuick.Controls
//import QtQuick.Controls.Basic
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Item {
    id: rootModalFileList

    property int maxFoldersDisplayed: 6
    property int maxFilesDisplayed: 10
    property string idFolderSelected: ApplicationController.idCurrentFolder
    property bool selectionMode: Constants.isFileSelectionMode

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

    Item {
        id: modalContentContainer
        anchors.centerIn: parent
        width: parent.width * 0.96
        height: parent.height * 0.85
        anchors.verticalCenterOffset: parent.height * -0.05
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

        /** Liste des fichiers */
        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true    

            /** Retour au dossier parent */
            RowLayout {
                id: lblParentFolder
                visible: idFolderSelected !== "/"

                anchors {
                    top: parent.top
                    left: parent.left
                }        

                Image {
                    Layout.preferredWidth: 50
                    Layout.alignment: Qt.AlignVCenter
                    source: Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireParent.svg")
                    fillMode: Image.PreserveAspectFit                    

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            ApplicationController.go_to_parent_folder()                            
                        }
                    }
                }
                
                Label
                {                                        
                    clip: true
                    color: Constants.colorText                    
                    text: "Dossier parent"
                    Layout.fillHeight: true
                    Layout.fillWidth: true                    
                    font.pointSize: 24
                    verticalAlignment: Text.AlignVCenter
                    elide: Label.ElideRight

                    MouseArea {
                        anchors.fill: parent
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
                clip: true
                property int rowHeight: 50
                model: Constants.fileList
                spacing: 20

                Component.onCompleted: {
                    listView.flickEnded.connect(snapToRow)
                }

                onContentYChanged: {
                    snapToRow()
                }

                function snapToRow() {
                    var totalRowHeight = listView.rowHeight + listView.spacing
                    var targetRow = Math.round(contentY / totalRowHeight)
                    var targetY = targetRow * totalRowHeight
                    if(contentY !== targetY) {
                        contentY = targetY
                    }
                }

                WheelHandler {
                    //property: "contentY"
                    onWheel: (event)=> {
                        var totalRowHeight = listView.rowHeight + listView.spacing
                        var delta = event.angleDelta.y > 0 ? -1 : 1
                        let targetRow = Math.round(listView.contentY / totalRowHeight) + delta
                        targetRow = Math.max(0, Math.min(targetRow, listView.count - 1))
                        listView.contentY = targetRow * totalRowHeight
                    }
                }

                flickableDirection: Flickable.VerticalFlick
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
                    height: visible ? listView.rowHeight : 0                    
                    width: listView.width *0.95
                    spacing: 10
                    
                    Image {
                        Layout.preferredWidth: parent.height 
                        Layout.preferredHeight: parent.height

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

                        onToggled: function() {
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
                    visible: Constants.fileList !== null ? Constants.fileList.count === 0 : false
                    color: Constants.colorText
                    anchors.fill: parent
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: "Veuillez insérer une clé USB"
                    font.pixelSize: width * 0.07
                }

                remove: Transition {
                    NumberAnimation {
                        properties: "x"
                        to: parent.width
                        duration: 200
                    }
                }

                removeDisplaced: Transition {
                    NumberAnimation {
                        properties: "y"
                        duration: 150
                    }
                }
            }
        }
    }
}
