import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Item {
    id: coreFileList

    property int maxItemDisplayed: 10
    //property var _fileList: ApplicationController.queueListProxyModel
    property var _fileList: ApplicationController.queueListModel
    property bool selectSaneFiles: false
    property bool selectionMode: false

    /*Connections {
        target: Constants

        onAnalyseFile: {
            Constants.addToAnalyse(type, name, selected, status, analyseProgress, backId)
        }

        onUpdateFileProgress: {
            for (let i = 0; i < Constants.runningFileList.count; i++)
            {
                var item = Constants.runningFileList.get(i)
                if (backId === item.backId)
                {
                    //item.progress = newProgress
                    Constants.runningFileList.setProperty(i, "progress", newProgress)
                    _fileList.setProperty(i, "progress", newProgress)
                    return;
                }
            }
        }

        onUpdateFileStatus: {
            for (let i = 0; i < Constants.runningFileList.count; i++)
            {
                var item = Constants.runningFileList.get(i)
                if (backId === item.backId)
                {
                    //item.status = newStatus
                    Constants.runningFileList.setProperty(i, "status", newStatus)
                    _fileList.setProperty(i, "status", newStatus)
                    return;
                }
            }
        }
        
        onClearRunningFileList: {
            Constants.runningFileList.clear()
        }
    }*/

    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(Constants.colorModePath  + "ContainerSupportEntree.svg")
    }

    function getTextColor(state)
    {
        switch (state)
        {
        case Enums.FileStatus.FileAnalysing:
            return Constants.colorBlue
        case Enums.FileStatus.FileClean:        
            return Constants.colorGreen
        case Enums.FileStatus.FileInfected:
        case Enums.FileStatus.FileCopyError:
        case Enums.FileStatus.FileAnalysisError:
            return Constants.colorRed
        default :
            return Constants.colorText
        }
    }

    function getStatusText(state) {
        switch (state)
        {
        case Enums.FileStatus.FileClean:
            return "Sain";
        case Enums.FileStatus.FileInfected:
            return "Infecté";
        case Enums.FileStatus.FileCopyError:
        case Enums.FileStatus.FileAnalysisError:
            return "Erreur"
        case Enums.FileStatus.FileCopySuccess:
            return "Copié"
        default:
            return "autre ("+state +")";
        }
    }

    Item {
        id: container
        width: parent.width * 0.92
        height: parent.height * 0.96
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: parent.width * 0.02
    }

    ColumnLayout {
        anchors {
            fill: container
            bottomMargin: parent.height*0.1
        }
        spacing: 20

        RowLayout {
            Layout.preferredHeight: 40
            Layout.fillWidth: true

            Label {
                Layout.alignment: Qt.AlignLeft
                text: "Filtre fichiers :"
                font.pixelSize: height
                color: Constants.colorText
            }

            CheckBox {
                id: chkFiltreSains
                Layout.preferredHeight: parent.height * 0.8
                Layout.preferredWidth: height
                checked: _fileList !== null ? _fileList.filtreSains : false

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

                onCheckedChanged: {
                    if(_fileList != null)
                        _fileList.filtreSains = checked
                }
            }

            Label {
                text: "Sains"
                font.pixelSize: height
                color: Constants.colorText
            }

            Item {
                Layout.fillWidth: true
            }

            CheckBox {
                id: chkFiltreInfectes

                Layout.preferredHeight: parent.height * 0.8
                Layout.preferredWidth: height
                checked: _fileList !== null ? _fileList.filtreInfectes : false

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

                onCheckedChanged: {
                    if(_fileList != null)
                        _fileList.filtreInfectes = checked
                }
            }

            Label {
                text: "Infectés"
                font.pixelSize: height
                color: Constants.colorText
            }

            Item {
                Layout.fillWidth: true
            }

            CheckBox {
                id: chkFiltreAutres

                Layout.preferredHeight: parent.height * 0.8
                Layout.preferredWidth: height
                checked: _fileList !== null ? _fileList.filtreAutres : false

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

                onCheckedChanged: {
                    if(_fileList != null)
                        _fileList.filtreAutres = checked
                }
            }

            Label {
                text: "Autres"
                font.pixelSize: height
                color: Constants.colorText
            }

            Item {
                Layout.fillWidth: true
            }
        }

        ListView {            
            id: fileListListView
            clip: true
            Layout.alignment: Qt.AlignCenter
            Layout.fillHeight: true
            Layout.fillWidth: true
            model: _fileList
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
                //property: "contentY"
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

            delegate : RowLayout {
                width: fileListListView.width *0.95
                height: fileListListView.rowHeight
                spacing: 10

                CheckBox
                {
                    visible: status === Enums.FileStatus.FileClean
                    Layout.preferredHeight: parent.height
                    Layout.preferredWidth: parent.height
                    checked: selected

                    contentItem: Image {
                        source: Qt.resolvedUrl(Constants.colorModePath  + "CaseACocherVerte.svg")
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
                }

                Label {
                    Layout.preferredHeight: parent.height
                    Layout.fillWidth: true
                    text: filename
                    color: getTextColor(status)
                    font.pointSize: 24
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                    elide: Label.ElideRight
                }

                Rectangle {
                    Layout.preferredHeight: parent.height
                    Layout.preferredWidth: fileListListView.width / 3
                    color: "transparent"
                    border.width: 2
                    border.color: Constants.colorBlue
                    visible: progress < 100

                    Rectangle {
                        width: Math.min(parent.width * progress/100, parent.width)
                        height: parent.height
                        color: Constants.colorBlue
                        opacity: 0.3
                    }

                    Label {
                        anchors.centerIn: parent
                        width: parent.width
                        height: parent.height
                        text: Math.round(progress) + "%"
                        color: Constants.colorBlue
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }                

                Label {
                    Layout.preferredWidth: fileListListView.width / 3
                    Layout.preferredHeight: parent.height
                    text: getStatusText(status)
                    color: getTextColor(status)
                    font.pointSize: 24
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                    elide: Label.ElideRight
                    visible: progress === 100
                }
            }
        }

    }

}
