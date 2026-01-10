import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components
import Saphir

Item {
    id: main    

    ColumnLayout  {
        id: colLyt

        anchors.fill: parent
        spacing: height * 0.1

        /* Progress */
        RowLayout {
            //Layout.fillHeight: true
            Layout.preferredHeight: parent.height * 0.5
            Layout.fillWidth: true
            spacing: height/20

            Item { Layout.fillWidth: true }

            PanelBase {
                radius: height
                Layout.preferredHeight: parent.height
                Layout.preferredWidth: parent.height

                FilesProgress {
                    anchors {
                        fill: parent
                        margins: 5
                    }

                }
            }

            Item { Layout.fillWidth: true }

            PanelBase {
                radius: height
                Layout.preferredHeight: parent.height
                Layout.preferredWidth: parent.height

                GlobalProgress {
                    anchors {
                        fill: parent
                        margins: 5
                    }
                }
            }

            Item { Layout.fillWidth: true }
        }

        PanelBase {
            Layout.preferredWidth: parent.width
            Layout.preferredHeight: parent.height * 0.5
            radius: 10

            ListView {
                id: fileListListView                
                anchors {
                    fill: parent
                    margins: parent.height * 0.05
                }
                clip: true

                model: bindings.sourceFilesListModel
                spacing: 10
                property int rowHeight: 25

                Component.onCompleted: {
                    fileListListView.flickEnded.connect(snapToRow)
                }

                onContentYChanged: {
                    if(!fileListListView.flicking && !fileListListView.moving) {
                        snapToRow()
                    }
                }

                function snapToRow() {
                    var totalRowHeight = fileListListView.rowHeight + fileListListView.spacing
                    var targetRow = Math.round(contentY / totalRowHeight)
                    var targetY = targetRow * totalRowHeight
                    if(contentY !== targetY) {
                        contentY = targetY
                    }
                }

                WheelHandler {
                    onWheel: (event)=> {
                        var totalRowHeight = fileListListView.rowHeight + fileListListView.spacing
                        var delta = event.angleDelta.y > 0 ? -1 : 1
                        let targetRow = Math.round(fileListListView.contentY / totalRowHeight) + delta
                        targetRow = Math.max(0, Math.min(targetRow, fileListListView.count - 1))
                        fileListListView.contentY = targetRow * totalRowHeight
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
                        border.color: Environment.colorText
                    }

                    contentItem: Rectangle {
                        implicitWidth: parent.parent.width*0.01
                        color: Environment.colorText  // Couleur de la barre de défilement
                        radius: 6
                    }
                }

                delegate : RowLayout {
                    width: fileListListView.width - scrollbar.width
                    height: fileListListView.rowHeight
                    spacing: 10

                    /*CheckBox
                    {
                        //visible: status === Enums.FileStatus.FileClean
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: parent.height
                        checked: status === Enums.FileStatus.FileClean
                        checkable: false

                        contentItem: Image {
                            //source: Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherVerte.svg")
                            source: status === Enums.FileStatus.FileClean ? Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherVerte.svg") : Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherActive.svg")
                            anchors.fill: parent
                            fillMode: Image.PreserveAspectFit
                        }

                        indicator: Image {
                            visible: parent.checked
                            source: Qt.resolvedUrl(Constants.colorModePath  + "CocheSain.svg")
                            fillMode: Image.PreserveAspectFit
                            width: parent.width*0.6
                            height: width
                            anchors.centerIn: parent
                        }
                    }

                    Item {
                        //Spacer pour aligner quand la checkbox n'est pas visible
                        Layout.preferredWidth: 10
                        visible: status !== Enums.FileStatus.FileClean
                    }*/

                    StyledText {
                        Layout.preferredHeight: parent.height
                        Layout.fillWidth: true
                        text: filename
                        color: getTextColor(status)
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        Layout.preferredHeight: parent.height
                        Layout.preferredWidth: fileListListView.width / 4
                        color: "transparent"
                        border.width: 2
                        border.color: Environment.colorBorder
                        visible: progress < 100

                        Rectangle {
                            width: Math.min(parent.width * progress/100, parent.width)
                            height: parent.height
                            color: Environment.colorBorder
                            opacity: 0.3
                        }

                        StyledText {
                            anchors.centerIn: parent
                            width: parent.width
                            height: parent.height
                            text: Math.round(progress) + "%"
                            color: Environment.colorText
                            font.pixelSize: Math.min(height * 0.6, width * 0.15)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    StyledText {
                        Layout.preferredWidth: fileListListView.width / 3
                        Layout.preferredHeight: parent.height
                        text: getStatusText(status)
                        color: getTextColor(status)
                        horizontalAlignment: Text.AlignLeft
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                        visible: progress === 100
                    }
                }

                add: Transition {
                    NumberAnimation {
                        properties: "x"
                        from: -width
                        to: 0
                        duration: 200
                    }
                }
            }
        }
    }

    /** Functions */
    function getTextColor(state) {
        switch (state) {
            case Enums.FileStatus.FileAnalysing:
                return Environment.colorWaiting
            case Enums.FileStatus.FileClean:
                return Environment.colorClean
            case Enums.FileStatus.FileInfected:
            case Enums.FileStatus.FileCopyError:
            case Enums.FileStatus.FileAnalysisError:
                return Environment.colorInfected
        }

        return Environment.colorText
    }

    function getStatusText(state) {
        switch (state) {
            case Enums.FileStatus.FileClean:
                return qsTr("Clean")
            case Enums.FileStatus.FileInfected:
                return qsTr("Infected")
            case Enums.FileStatus.FileCopyError:
            case Enums.FileStatus.FileAnalysisError:
                return qsTr("Error")
            case Enums.FileStatus.FileCopySuccess:
                return qsTr("Copied")
        }

        return qsTr("Other") +" ("+state +")";
    }
}
