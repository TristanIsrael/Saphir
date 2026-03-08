import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components

SimpleDialog {
    id: root

    buttonsLabels: [ qsTr("Close") ]
    overlay: true

    contentItem: Item {
        width: Environment.mainWidth * 0.75
        height: Environment.mainHeight * 0.7

        ColumnLayout {
            anchors {
                fill: parent
                margins: height * 0.05
            }

            spacing: 20

            StyledText {
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                text: qsTr("System log")
                section: Constants.Section.Title1
            }

            TableView {
                id: viewLog
                Layout.fillHeight: true
                Layout.fillWidth: true
                rowSpacing: 5
                columnSpacing: 20
                clip: true
                flickableDirection: Flickable.VerticalFlick

                model: bindings.logModel
                columnWidthProvider: function(column) {
                    switch(column) {
                        case 0: return fontMetrics.boundingRect("99:99:99.999").width
                        case 1: return fontMetrics.boundingRect("AnalysisController").width
                        case 2: return viewLog.width - columnWidthProvider(0) - columnWidthProvider(1)
                    }
                }
                delegate: StyledText {                    
                    text: display
                }
            }
        }
    }

    FontMetrics {
        id: fontMetrics
        font.family: "Inter"
        font.pixelSize: 18
    }

    Bindings {
        id: bindings
    }
}
