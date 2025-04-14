import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet
import "../../imports"


Rectangle {
    id: coreFileList
    color: "transparent"

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
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportEntree.svg")
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

    /*function toggleSaneFiles()
    {
        coreFileList.selectSaneFiles = !coreFileList.selectSaneFiles
        for (let i = 0; i < _fileList.count; i++) {
            if (_fileList.get(i).status === Constants.FileState.SANE)
            {
                _fileList.setProperty(i, "selected", coreFileList.selectSaneFiles)
            }
        }

    }*/

    Rectangle {
        id: container
        width: parent.width * 0.92
        height: parent.height * 0.96
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: parent.width * 0.02
        color: "transparent"
    }

    ColumnLayout {
        anchors {
            fill: container
            //topMargin: parent.height*0.01
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
                checked: _fileList.filtreSains

                background: Item {}

                contentItem: Image {
                    source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherActive.svg")
                    //anchors.centerIn: parent
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

                onCheckedChanged: {
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
                checked: _fileList.filtreInfectes

                background: Item {}

                contentItem: Image {
                    source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherActive.svg")
                    //anchors.centerIn: parent
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

                onCheckedChanged: {
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
                checked: _fileList.filtreAutres

                background: Item {}

                contentItem: Image {
                    source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherActive.svg")
                    //anchors.centerIn: parent
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

                onCheckedChanged: {
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

        /*Rectangle {
            Layout.preferredHeight: 40
            Layout.fillWidth: true
            color: "transparent"

            Row {
                width: parent.width
                height: parent.height

                CheckBox
                {
                    width: parent.width * 0.1
                    height: parent.height
                    id: checkBox

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
                        width: height
                        height: parent.height * 0.6
                    }

                    onCheckedChanged: function() {
                        if(checked) {
                            ApplicationController.select_all_clean_files_for_copy()
                        } else {
                            ApplicationController.deselect_all_clean_files_for_copy()
                        }
                    }
                }

                Label {
                    height: parent.height
                    width: parent.width * 0.9

                    text: "Sélectionner tous les fichiers sains"
                    color: Constants.colorText
                    font.pixelSize:  Math.min(height * 0.6, width * 0.15)
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }

            }
        }*/

        ListView {            
            id: fileListListView
            clip: true
            Layout.alignment: Qt.AlignCenter
            //Layout.preferredHeight: 90
            Layout.fillHeight: true
            Layout.fillWidth: true
            model: _fileList
            spacing: 10

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
                //width: parent.width*0.95
                //height: parent.parent.height * (1.0/maxItemDisplayed)
                height: 25
                spacing: 10

                CheckBox
                {
                    visible: status === Enums.FileStatus.FileClean
                    Layout.preferredHeight: parent.height
                    Layout.preferredWidth: parent.height
                    checked: selected

                    contentItem: Image {
                        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherVerte.svg")
                        anchors.fill: parent                 
                        fillMode: Image.PreserveAspectFit
                    }

                    indicator: Image {
                        visible: parent.checked                        
                        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CocheSain.svg")                        
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
                    //property real progress: 0.0
                    //anchors.centerIn : parent.parent

                    //width: parent.parent.width
                    //height: parent.parent.parent.height
                    Layout.preferredHeight: parent.height
                    Layout.preferredWidth: fileListListView.width / 3
                    //Layout.fillWidth: true
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

    /*Component {
        id: loadingBar

        Rectangle {
            property real progress: 0.0
            anchors.centerIn : parent.parent
            width: parent.parent.width
            height: parent.parent.parent.height
            color: "transparent"
            border.width: height * 0.1
            border.color: Constants.colorBlue

            Rectangle {
                width: Math.min(parent.width * progress, parent.width)
                height: parent.height
                color: Constants.colorBlue
                opacity: 0.3
            }

            Label {
                anchors.centerIn: parent
                width: parent.width
                height: parent.height
                text: Math.round(progress * 100.0) + "%"
                color:  Constants.colorBlue
                font.pixelSize: Math.min(height * 0.6, width * 0.15)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }*/

    /*Component {
        id: textStatus
        
    }*/

    //Test de barre de chargement
    //property real tmpProgress: 0.5
    // property real tmp2Progress: 0.2
    // Timer {
    //     interval: 1000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         //Constants.updateFileProgress(7, tmpProgress+= 0.01)
    //         Constants.updateFileProgress(8, tmp2Progress+= 0.01)
    //     }
    // }

    // //Test de changement de status
    // property int tmpStatus: 0
    // Timer {
    //     interval: 2000
    //     running: true
    //     repeat: true

    //     onTriggered: {
    //         Constants.updateFileStatus(7, tmpStatus = (tmpStatus + 1) % 4)
    //     }
    // }

}
