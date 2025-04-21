import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import net.alefbet
import "../../imports"

Item {
    id: coreEtatLogs        

    Item {
        anchors.fill: parent
        
        Image {
            id: background            
            source: Qt.resolvedUrl(Constants.colorModePath  + "Modale.png")
            fillMode: Image.Stretch
            anchors.fill: parent
        }

        DropShadow {
            anchors.fill: background
            source: background
            radius: 20
            color: "#333"
            cached: true
        }
    }

    Image {
        id: returnButton
        source: Qt.resolvedUrl(Constants.colorModePath  + "FermerModale.png")
        height: parent.height * 0.12
        width: parent.width * 0.075
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: (parent.width * 0.02) + (width * 0.5)
        
        MouseArea {
            anchors.fill: parent
            onClicked: coreEtatLogs.visible = !coreEtatLogs.visible
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

    ColumnLayout {
        anchors.fill: modalContentContainer

        Rectangle {
            id: modalTitleHolder
            Layout.preferredHeight: parent.height/7
            Layout.fillWidth: true
            Layout.margins: height/10
            color: "transparent"

            border {
                width: width * 0.005
                color: Constants.colorText
            }
            radius: height/5

            RowLayout {
                anchors.centerIn: parent
                width: parent.width - (parent.border.width * 3)
                height: parent.height- (parent.border.width * 3)

                Item {
                    Layout.fillWidth: true
                }

                Image {
                    Layout.fillHeight: true
                    Layout.margins: height/10
                    source: Qt.resolvedUrl(Constants.colorModePath  + "IconeRepertoireUnitaire.png")
                    fillMode: Image.PreserveAspectFit
                }

                Item {
                    Layout.preferredWidth: parent.height/2
                }

                Label {
                    id: modalTitleText
                    //width: parent.width
                    Layout.preferredHeight: parent.height
                    text: "Journal"
                    color: Constants.colorText
                    font.pixelSize: height*0.7
                    //horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                Item {
                    Layout.fillWidth: true
                }
            }
        }

        TableView {
            id: logsListView

            property int rowHeight: 40

            clip: true
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.margins: 10
            columnSpacing: 20
            rowSpacing: 20
                        
            //rowHeightProvider: function(row) { return logsListView.rowHeight }

            Component.onCompleted: {
                logsListView.flickEnded.connect(snapToRow)
            }

            onContentYChanged: {
                if(!logsListView.flicking && !logsListView.moving) {
                    snapToRow()
                }
            }

            function snapToRow() {
                var totalRowHeight = logsListView.rowHeight + logsListView.rowSpacing
                var targetRow = Math.round(contentY / totalRowHeight)
                var targetY = targetRow * totalRowHeight
                if(contentY !== targetY) {
                    contentY = targetY
                }
            }

            WheelHandler {
                //property: "contentY"
                onWheel: (event)=> {
                    var totalRowHeight = logsListView.rowHeight + logsListView.rowSpacing
                    var delta = event.angleDelta.y > 0 ? -1 : 1
                    let targetRow = Math.round(logsListView.contentY / totalRowHeight) + delta
                    targetRow = Math.max(0, Math.min(targetRow, logsListView.rows - 1))

                    logsListView.contentY = targetRow * totalRowHeight
                }
            }

            model: ApplicationController.logListModel

            flickableDirection: Flickable.VerticalFlick
            ScrollBar.vertical: ScrollBar
            {
                policy: parent.contentHeight > parent.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                width: parent.width*0.03
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

            delegate : Item {
                implicitHeight: logsListView.rowHeight
                implicitWidth: lbl.width

                Label {
                    id: lbl                    
                    clip: true
                    text: display
                    color: Constants.colorText
                    font.pixelSize: parent.height
                    elide: Label.ElideRight
                }
            }
        }
    }
}