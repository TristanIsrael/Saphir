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
                text: qsTr("System state")
                section: Constants.Section.Title1
            }

            StyledText {
                text: qsTr("Components state")
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter
                color: "transparent"
                border.color: Environment.colorBorder
                radius: 10

                TableView {
                    id: viewComponents
                    anchors {
                        fill: parent
                        margins: 10
                    }
                    rowSpacing: 5
                    columnSpacing: 20

                    model: bindings.componentsModel

                    delegate: RowLayout {
                        StyledText {
                            width: viewComponents.width
                            height: 20
                            text: display
                            visible: column > 0
                            font.bold: column === 1
                        }

                        Icon {
                            width: viewComponents.width
                            height: 20
                            text: {
                                if(column === 0) {
                                    if(display === "core") return Constants.iconCore
                                    if(display === "antivirus") return Constants.iconAntivirus
                                }

                                return Constants.iconHelp
                            }
                            visible: column === 0
                        }
                    }
                }
            }

            StyledText {
                text: qsTr("System information")
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter
                color: "transparent"
                border.color: Environment.colorBorder
                radius: 10

                TableView {
                    id: viewSystemInformation
                    anchors {
                        fill: parent
                        margins: 10
                    }
                    rowSpacing: 5
                    columnSpacing: 20

                    model: bindings.systemInformationModel

                    delegate: StyledText {
                        width: viewSystemInformation.width
                        height: 20
                        text: display
                        font.bold: column === 0
                    }
                }
            }
        }
    }

    Bindings {
        id: bindings
    }
}
