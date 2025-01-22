import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import net.alefbet

Rectangle {
    id: root

    property alias tblView: tblView
    property alias model: tblView.model
    property alias pnlDigits: pnlDigits

    color: Constants.contrastColor
    implicitHeight: 500
    implicitWidth: 400

    Rectangle {
        id: entete
        anchors {
            left: parent.left
            top: parent.top
            right: parent.right
        }
        implicitHeight: 50

        color: Constants.headingColor

        RowLayout {
            anchors.centerIn: parent

            Icone {
                id: icnUsb
                text: "\ue05f" //f02f, e6b3, e241
                color: Constants.contrastColor
            }

            PText {
                id: lblDriveName
                font.capitalization: Font.SmallCaps
                text: globalProgressLabel()
                color: Constants.contrastColor
            }
        }
    }

    TableView {
        id: tblView

        model: ApplicationController.queueListModel

        clip: true
        anchors {
            top: entete.bottom
            topMargin: 10
            left: parent.left
            right: parent.right
            bottom: pnlDigits.top
            bottomMargin: 10
        }

        //visible: globalProgress > 0
        rowSpacing: 0
        ScrollBar.vertical: ScrollBar {
            id: scrollbar
            policy: ScrollBar.AsNeeded
        }

        delegate: Rectangle {
            implicitWidth: tblView.width - scrollbar.width
            implicitHeight: 40
            //visible: inqueue
            //implicitHeight: progress < 100 ? 40 : 0.00001

            Rectangle {
                implicitHeight: parent.height
                implicitWidth: parent.width * (progress / 100)
                color: textbackgroundColor(status, progress)
                /*border {
                    width: status == Enums.FileStatus.FileAnalysing ? 2 : 0
                    color: Constants.headingColor
                }*/
            }

            PText {
                text: filepath
                level: PText.TextLevel.Paragraph
                color: textColor(status, progress)
                    //status === Enums.FileStatus.FileStatusUndefined ? Constants.disabledColor : progress === 100 ? Constants.contrastColor : Constants.textColor
                elide: Text.ElideMiddle

                /*Component.onCompleted: function() {
                    console.debug(status, Enums.FileStatus.FileStatusUndefined, status === Enums.FileStatus.FileStatusUndefined)
                }*/

                anchors {
                    left: parent.left
                    leftMargin: 10
                    top: parent.top
                    bottom: parent.bottom
                    right: icnDel.left
                    rightMargin: 5
                }
                verticalAlignment: Text.AlignVCenter
            }

            Icone {
                id: icnDel
                text: "\ueb80"
                color: Constants.intermediateColor
                anchors {
                    right: parent.right
                    rightMargin: 5
                    verticalCenter: parent.verticalCenter
                }
                visible: (mAreaItem.containsMouse || mAreaDel.containsMouse) && progress === 0
                pixelSize: 40                    

                Connections {
                    function onClicked() {                            
                        //const fpath = filepath +(filepath === "/" ? "" : "/") +filename
                        ApplicationController.dequeue_file(filepath) 
                    }
                }
            }

            MouseArea {
                id: mAreaDel
                anchors.fill: icnDel
                hoverEnabled: true     
                propagateComposedEvents: true                    
            } 

            MouseArea {
                id: mAreaItem
                hoverEnabled: true

                anchors {
                    left: parent.left
                    top: parent.top
                    bottom: parent.bottom
                    right: icnDel.left
                }                
            }
        }
    }

    ResultDigitsPanel {
        id: pnlDigits

        height: parent.width / 6
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            //left: parent.left
            //right: parent.right
        }
    }

    // Functions
    function textbackgroundColor(status, progress) { 
        switch(status) {
            case Enums.FileStatus.FileStatusUndefined: return Constants.contrastColor
            case Enums.FileStatus.FileAvailableInRepository: return Constants.selectionColor
            case Enums.FileStatus.FileClean: return Constants.successColor
            case Enums.FileStatus.FileInfected: return Constants.errorColor
            case Enums.FileStatus.FileAnalysing: return Constants.selectionColor
            case Enums.FileStatus.FileAnalysisError: return Constants.selectionColor
            default: return Constants.contrastColor
        }                    
    }

    function textColor(status, progress) {
        switch(status) {
            case Enums.FileStatus.FileStatusUndefined: return Constants.disabledColor
            case Enums.FileStatus.FileAvailableInRepository: return Constants.textColor
            case Enums.FileStatus.FileClean: return Constants.contrastColor
            case Enums.FileStatus.FileInfected: return Constants.contrastColor   
            case Enums.FileStatus.FileAnalysing: return Constants.textColor   
            case Enums.FileStatus.FileAnalysisError: return Constants.errorColor      
            default: return Constants.textColor
        }
    }

    function globalProgressLabel() {
        if(ApplicationController.globalProgress > 0) {
            if(ApplicationController.globalProgress === 100) {
                return qsTr("Analyse terminée")
            }            
            return qsTr("Analyse en cours (%1 %)").arg(ApplicationController.globalProgress)
        } else { 
            return qsTr("Aucune analyse en cours")
        }
    }
}