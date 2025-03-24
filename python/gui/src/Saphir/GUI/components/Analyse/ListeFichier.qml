import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../imports"


Rectangle {
    id: coreFileList
    color: "transparent"

    property int maxItemDisplayed: 10
    property ListModel _fileList
    property bool selectSaneFiles: false
    property bool selectionMode: false

    Connections {
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
    }

    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "ContainerSupportEntree.svg")
    }

    function getTextColor(state)
    {
        switch (state)
        {
        case Constants.FileState.ANALYSING:
            return Constants.colorBlue;
        case Constants.FileState.SANE:
            return Constants.colorGreen;
        case Constants.FileState.INFECTED:
            return Constants.colorRed;
        default :
            return Constants.colorText;
        }
    }

    function getStatusText(state) {
        switch (state)
        {
        case Constants.FileState.SANE:
            return "Sain";
        case Constants.FileState.INFECTED:
            return "Infecté";
        default :
            return "";
        }
    }

    function toggleSaneFiles()
    {
        coreFileList.selectSaneFiles = !coreFileList.selectSaneFiles
        for (let i = 0; i < _fileList.count; i++) {
            if (_fileList.get(i).status === Constants.FileState.SANE)
            {
                _fileList.setProperty(i, "selected", coreFileList.selectSaneFiles)
            }
        }

    }

    Rectangle {
        id: container
        width: parent.width * 0.92
        height: parent.height * 0.96
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: parent.width * 0.02
        color: "transparent"
    }

    ColumnLayout {
        anchors.fill: container

        Rectangle {
            Layout.preferredHeight: 10
            Layout.fillHeight: true
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
                    visible: true
                    checked: model.selected = checked
                    onCheckedChanged: { toggleSaneFiles() }
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
                        width: parent.width*0.5
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
        }

        Rectangle {
            Layout.preferredHeight: 90
            Layout.fillHeight: true
            Layout.fillWidth: true
            color: "transparent"
            ListView {
                clip: true
                id: fileListListView
                Layout.alignment: Qt.AlignCenter
                width: parent.width
                height: parent.height
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

                delegate : RowLayout {
                    width: parent.width*0.95
                    height: parent.parent.height * (1.0/maxItemDisplayed)
                    spacing: 0

                    CheckBox
                    {
                        Layout.preferredWidth: 10
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;

                        visible: model.status === Constants.FileState.SANE
                        checked: model.selected
                        onCheckedChanged: model.selected = checked
                        contentItem: Image {
                            anchors.verticalCenter: parent.verticalCenter
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CaseACocherVerte.svg")
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            Layout.fillHeight: true
                        }
                        indicator: Image {
                            visible: parent.checked
                            anchors.verticalCenter: parent.verticalCenter
                            source: Qt.resolvedUrl(Constants.colorModePath + Constants.colorModePrefix + "CocheSain.svg")
                            anchors.horizontalCenter: parent.horizontalCenter
                            fillMode: Image.PreserveAspectFit
                            width: parent.width*0.5
                        }
                    }

                    Item {
                        //Spacer pour aligner quand la checkbox n'est pas visible
                        Layout.preferredWidth: 10
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;
                        visible: model.status !== Constants.FileState.SANE
                    }

                    Label {
                        Layout.preferredWidth: 50
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;
                        text: model.name
                        color: getTextColor(model.status)
                        font.pixelSize: Math.min(height * 0.6, width * 0.15)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Label.ElideRight
                    }

                    Rectangle {
                        Layout.preferredWidth: 40
                        Layout.fillHeight: true;
                        Layout.fillWidth: true;
                        color: "transparent"

                        Loader {
                            id: loader
                            width: parent.width
                            height: parent.height * 0.6
                            anchors.centerIn: parent
                            sourceComponent: model.status === Constants.FileState.ANALYSING ? loadingBar : textStatus
                            onLoaded: {
                                if (model.status === Constants.FileState.ANALYSING)
                                {
                                    item.progress = model.progress
                                }
                                else {
                                    item.displayText = getStatusText(model.status)
                                    item.displayTextColor = getTextColor(model.status)
                                }
                            }
                            Binding {
                                when: model.status === Constants.FileState.ANALYSING
                                target: loader.item
                                property: "progress"
                                value: model.progress
                            }
                            Binding {
                                when: model.status !== Constants.FileState.ANALYSING
                                target: loader.item
                                property: "displayText"
                                value: getStatusText(model.status)
                            }
                            Binding {
                                when: model.status !== Constants.FileState.ANALYSING
                                target: loader.item
                                property: "displayTextColor"
                                value: getTextColor(model.status)
                            }
                        }

                    }


                }
            }
        }

    }

    Component {
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
    }

    Component {
        id: textStatus
        Label {
            property string displayText: ""
            property string displayTextColor: ""
            anchors.centerIn: parent.parent
            width: parent.parent.width
            height: parent.parent.height
            text: displayText
            color: displayTextColor
            font.pixelSize:  Math.min(height * 0.8, width * 0.3)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Label.ElideRight
        }
    }

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
