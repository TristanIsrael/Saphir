import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Pdf
import Components
import Saphir

PanelBase {
    id: root

    property string filePath: bindings.currentFilepath
    property int fileType: bindings.currentFiletype

    onFilePathChanged: function() {
        console.debug(filePath)
    }
    
    width: implicitWidth
    height: implicitHeight
    implicitWidth: Environment.mainWidth * 0.9
    implicitHeight: Environment.mainHeight * 0.9
    radius: 10

    Item {
        anchors {
            top: parent.top 
            left: parent.left
            right: parent.right 
            bottom: btnClose.top
            margins: 10
        }
        clip: true

        Image {
            id: img            

            width: Math.min(implicitWidth, parent.width)
            height: Math.min(implicitHeight, parent.height)
            fillMode: Image.PreserveAspectFit
            source: visible ? bindings.repositoryPath + root.filePath : ""
            visible: root.fileType === Enums.Image && root.filePath !== ""
        }

        PdfMultiPageView {
            id: pdf

            anchors {
                fill: parent
            }

            visible: root.fileType === Enums.Pdf && root.filePath !== ""
            onVisibleChanged: function() {
                console.debug(visible, pdfDocument.source, root.filePath)
            }

            document: PdfDocument {
                id: pdfDocument
                source: pdf.visible ? root.filePath : ""
            }
        }

        MediaViewer {
            id: mediaViewer

            anchors {
                fill: parent
            }

            visible: root.fileType === Enums.Video || root.fileType === Enums.Audio
            filePath: root.filePath
        }
        
    }

    StyledText {
        id: lblProgress        
        horizontalAlignment: Qt.AlignHCenter

        anchors {
            top: parent.top
            topMargin: 10
            horizontalCenter: parent.horizontalCenter
        }
        width: parent.width / 3
        height: 30

        text: bindings.currentStep
        visible: img.status !== Image.Ready
    }

    FlatButton {
        id: btnClose

        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: 10
        }

        label: qsTr("Close")

        Connections {
            function onClicked() {
                root.visible = false
            }
        }
    }

    Bindings {
        id: bindings
    }
    
}
