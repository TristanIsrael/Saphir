import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Components
import Saphir

Item {
    id: main

    width: implicitWidth
    height: implicitHeight
    implicitWidth: Environment.mainWidth * 0.9
    implicitHeight: Environment.mainHeight * 0.9

    ColumnLayout  {
        id: colLyt

        anchors.fill: parent
        spacing: height * 0.05

        PanelBase {
            id: pnlHeader
            Layout.preferredWidth: parent.width
            Layout.preferredHeight: 150
            radius: 10

            /* Header */
            ColumnLayout {
                width: parent.width - 20
                height: parent.height - 20
                x: 10
                y: 10
                spacing: height/20

                StyledText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: qsTr("Only clean files will be copied. The copy will begin as soon as you connect a new storage.")
                }

                StyledText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Environment.colorWarning
                    text: qsTr("Please keep the source storage connected during the file copy.")
                }

                RowLayout {
                    Layout.fillHeight: true
                    Layout.maximumHeight: 30
                    Layout.fillWidth: true

                    StyledText {
                        text: qsTr("Volume of files to copy: %1").arg(formatFileSize(bindings.cleanFilesSize))
                        section: Constants.Section.Tiny
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    ColumnLayout {

                        StyledText {
                            text: qsTr("Destination: %1").arg(bindings.targetName)
                            section: Constants.Section.Tiny
                        }

                        StyledText {
                            text: qsTr("Available space: Unknown") //.arg(formatFileSize(bindings.targetAvailableSize))
                            section: Constants.Section.Tiny
                        }
                    }
                }

                StyledText {
                    Layout.fillWidth: true
                    text: {
                        if(bindings.targetName === "") {
                            return qsTr("Please connect a storage...")
                        } else {
                            // Transfer in progress
                            if(bindings.systemState === Enums.CopyCleanFiles) {
                                return qsTr("Copy in progress...")
                            } else if (bindings.systemState === Enums.GeneratingReport) {
                                return qsTr("Generating the report...")
                            } else if (bindings.systemState === Enums.TransferFinished) {
                                return qsTr("The transfer is finished!")
                            }
                        }

                        return qsTr("Undefined (%1)").arg(bindings.systemState)
                    }
                    horizontalAlignment: Qt.AlignHCenter
                    color: {
                        if(bindings.targetName === "") {
                            return Environment.colorWarning
                        } else {
                            // Transfer in progress...
                            if([Enums.CopyCleanFiles, Enums.GeneratingReport].includes(bindings.systemState)) {
                                return Environment.colorText
                            } else if (bindings.systemState === Enums.GeneratingReport) {
                                return Environment.colorText
                            } else if (bindings.systemState === Enums.TransferFinished) {
                                return Environment.colorClean
                            }
                        }

                        return qsTr("Undefined (%1)").arg(bindings.systemState)
                    }

                    section: Constants.Section.Title2
                }

            }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillHeight: true
            Layout.maximumHeight: parent.height/2
            Layout.fillWidth: true
            spacing: height/20

            Item { Layout.fillWidth: true }

            PanelBase {
                Layout.preferredWidth: height
                Layout.preferredHeight: parent.height
                radius: height

                FilesProgress {
                    currentValue: bindings.nbCopied
                    maximumValue: bindings.nbClean

                    anchors {
                        fill: parent
                        margins: 5
                    }
                }
            }

            Item { Layout.fillWidth: true }
        }

        Item { Layout.fillHeight: true }
    }

    Bindings {
        id: bindings
    }

    function formatFileSize(bytes) {
        if (bytes < 1024)
            return bytes + qsTr(" B")
        else if (bytes < 1024 * 1024)
            return (bytes / 1024).toFixed(1) + qsTr(" KB")
        else if (bytes < 1024 * 1024 * 1024)
            return (bytes / (1024 * 1024)).toFixed(1) + qsTr(" MB")
        else
            return (bytes / (1024 * 1024 * 1024)).toFixed(1) + qsTr(" GB")
    }
}
