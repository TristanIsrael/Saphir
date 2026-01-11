import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components
import Saphir

PanelBase {
    id: root

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

                text: qsTr("Storage name: ") +bindings.sourceName
            }

            Item { Layout.fillWidth: true }

            StyledText {
                section: Constants.Section.Title1

                text: qsTr("Files in queue: ") +bindings.queueSize
            }
        }

        /* Fil d'Ariane */
        StyledText
        {            
            Layout.fillWidth: true
            text: qsTr("Current folder: ") +bindings.currentFolder
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideLeft
        }

        /** Retour au dossier parent */
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

        /*Item {
            Layout.preferredHeight: 10
        }*/

        ListView
        {
            id: listView
            clip: true
            property int rowHeight: 40
            Layout.preferredHeight: 40
            Layout.fillWidth: true
            Layout.fillHeight: true

            model: bindings.sourceFilesListModel
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
                height: visible ? listView.rowHeight : 0
                width: listView.width - scrollbar.width *2
                color: inqueue ? Environment.colorSelected : "transparent"
                
                RowLayout {
                    id: lyt
                    anchors.fill: parent
                    spacing: 10                

                    Icon {
                        Layout.preferredWidth: parent.height *0.8
                        Layout.preferredHeight: parent.height *0.8

                        text: type === "file" ? Constants.iconFile : Constants.iconFolder

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
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        section: Constants.Section.Title2

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

                    Icon {
                        Layout.preferredWidth: parent.height *0.8
                        Layout.preferredHeight: parent.height *0.8

                        text: inqueue ? Constants.iconChecked : Constants.iconUnchecked

                        MouseArea {
                            anchors.fill: parent

                            onClicked: function(mouse) {
                                if(inqueue) {
                                    bindings.removeFromQueue(type, filepath)
                                } else {
                                    bindings.addToQueue(type, filepath)
                                }
                            }
                        }
                    }                

                    /*CheckBox {
                        id: checkBox
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: parent.height
                        checked: selected

                        background: Item {}

                        contentItem: Image {
                            source: Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherActive.svg")
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
                                bindings.addToQueue(type, filename)
                            } else {
                                bindings.removeFromQueue(type, filename)
                            }
                        }
                    }*/
                }

                /*MouseArea {
                    anchors.fill: parent
                    propagateComposedEvents: true

                    onClicked: function(mouse) {
                        if(type !== "file") {
                            mouse.accepted = false
                            return
                        }

                        if(inqueue) {
                            bindings.removeFromQueue(type, filepath)
                        } else {
                            bindings.addToQueue(type, filepath)
                        }

                        mouse.accepted = true
                    }
                }*/

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

    /** Functions */
    function goToFolder(folderName) {
        const currentFolder = ApplicationController.currentFolder
        bindings.goToFolder((currentFolder === "/" ? "" : currentFolder) +"/" +folderName)
    }
}
