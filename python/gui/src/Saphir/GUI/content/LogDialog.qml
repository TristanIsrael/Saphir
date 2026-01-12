import QtQuick
import QtQuick.Layouts
import Components

SimpleDialog {
    id: root

    buttonsLabels: [ qsTr("Close") ]
    overlay: true

    contentItem: Item {
        implicitWidth: Environment.mainWidth * 0.5
        implicitHeight: Environment.mainHeight * 0.7

        ColumnLayout {
            anchors {
                fill: parent
                margins: height * 0.05
            }

            spacing: 10

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

                model: bindings.logModel

                delegate: RowLayout {
                    StyledText {
                        width: viewLog.width
                        height: 20
                        text: display
                    }
                }
            }
        }
    }

    Bindings {
        id: bindings
    }
}
