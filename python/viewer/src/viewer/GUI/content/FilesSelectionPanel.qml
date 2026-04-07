import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components
import Saphir

PanelBase {
    id: root

    signal viewFile(string filepath)

    width: implicitWidth
    height: implicitHeight
    implicitWidth: Environment.mainWidth * 0.9
    implicitHeight: Environment.mainHeight * 0.9
    radius: 10

    ColumnLayout {
        anchors {
            fill: parent
            margins: height * 0.025
        }
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: lblStorageName.height

            StyledText {
                id: lblStorageName
                section: Constants.Section.Title1

                text: qsTr("Storage name: ")
            }

            StyledComboBox {
                id: comboStorages
                model: bindings.disksList                   

                onActivated: {                    
                    ApplicationController.on_disk_selected(comboStorages.currentValue)
                }

                Component.onCompleted: {
                    currentIndex = comboStorages.indexOfValue(ApplicationController.currentDisk)
                }
            }


            Item { Layout.fillWidth: true }            
        }        

        /** Back to the parent folder */
        RowLayout {
            id: lblParentFolder
            visible: bindings.currentFolder !== "/"

            Layout.preferredWidth: parent.width
            Layout.alignment: Qt.AlignBottom
            Layout.preferredHeight: 40
            spacing: 10

            Icon {
                Layout.preferredWidth: 25
                Layout.alignment: Qt.AlignVCenter
                text: Constants.iconFolderUp

                MouseArea {
                    anchors.fill: parent
                    onClicked: {                        
                        bindings.goToParentFolder()
                    }
                }
            }

            StyledText
            {
                text: qsTr("Folder up")
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                section: Constants.Section.Title2

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        bindings.goToParentFolder()
                    }
                }
            }
        }

        ListView
        {
            id: listView
            clip: true
            property int rowHeight: Environment.handheld ? 50 : 40
            Layout.fillWidth: true
            Layout.fillHeight: true

            model: bindings.inputFilesListModel
            spacing: 10

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
                id: scrollbar

                policy: parent.contentHeight > parent.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                width:parent.width*0.03
                background: Rectangle {
                    implicitWidth: parent.parent.width*0.01
                    color: "#00000000"  // Couleur du fond de la scrollbar
                    radius: 6
                    border.color: Environment.colorControl
                }

                contentItem: Rectangle {
                    implicitWidth: parent.parent.width*0.01
                    color: Environment.colorControl
                    radius: 6
                }
            }

            delegate: Rectangle {                
                height: visible ? listView.rowHeight : 0 //(Environment.handheld ? listView.rowHeight*1.5 : listView.rowHeight) : 0
                width: listView.width - scrollbar.width *2
                color: "transparent"
                
                RowLayout {
                    id: lyt
                    anchors.fill: parent
                    spacing: 10                

                    Icon {
                        Layout.preferredWidth: parent.height *0.8
                        Layout.preferredHeight: parent.height *0.8

                        text: type === "file" ? Constants.iconFile : Constants.iconFolder
                        color: type === "file" ? Environment.colorIconFile : Environment.colorIconFolder

                        MouseArea {
                            anchors.fill: parent
                            enabled: type === "folder"
                            onClicked: (mouse) => {
                                root.goToFolder(filename)
                            }
                        }
                    }

                    StyledText
                    {
                        clip: true
                        text: filename
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignLeft
                        elide: type === "file" || type === "folder" ? Text.ElideMiddle : Text.ElideRight
                        Layout.fillWidth: true
                        font.pixelSize: parent.height*0.7

                        MouseArea {
                            anchors.fill: parent
                            enabled: type === "folder"
                            onClicked: (mouse) => {
                                root.goToFolder(filename)
                            }                        
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    FlatButton {
                        id: btnViewFile
                        label: qsTr("View")
                        Layout.preferredHeight: parent.height*0.8
                        
                        Connections {
                            function onClicked() {
                                root.viewFile(filepath)
                            }
                        }
                    }
                }         
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

    Bindings {
        id: bindings
    }

    /** Slots */
    function onVisibleChanged() {
        if(visible && ApplicationController.sourceReady) {
            ApplicationController.update_source_files_list()
        }
    }

    Connections {
        target: ApplicationController

        /*function onCurrentDiskChanged() {
            console.debug("current disk=", ApplicationController.currentDisk)
            comboStorages.currentIndex = comboStorages.indexOfValue(ApplicationController.currentDisk)
        }*/
    }

    /** Functions */
    function goToFolder(folderName) {
        const currentFolder = ApplicationController.currentFolder
        bindings.goToFolder((currentFolder === "/" ? "" : currentFolder) +"/" +folderName)
    }
}
