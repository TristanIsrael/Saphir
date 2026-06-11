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

    PanelBase {
        id: pnlHeader
        width: parent.width
        height: lytHeader.height + lytHeader.y*2
        radius: 10

        /* Header */
        ColumnLayout {
            id: lytHeader
            width: parent.width - 20
            x: 10
            y: 10
            spacing: height/20

            StyledText {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("Only the clean files will be copied.")
                section: Constants.Section.Title3
            }

            StyledText {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                color: Environment.colorWarning
                text: qsTr("Please keep the source storage connected during the copy.")
                section: Constants.Section.Title2
                font.bold: true
            }

            Item {
                Layout.preferredHeight: 10
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

            Item {
                Layout.preferredHeight: 10
            }

            StyledText {
                Layout.fillWidth: true
                text: {
                    if(bindings.targetName === "" && bindings.systemState === Enums.AnalysisCompleted) {
                        return qsTr("Please connect a target storage...")
                    } else {
                        // Transfer in progress
                        if(bindings.systemState === Enums.CopyCleanFiles) {
                            return qsTr("Copy in progress...")
                        } else if (bindings.systemState === Enums.GeneratingReport) {
                            return qsTr("Generating the report...")
                        } else if (bindings.systemState === Enums.TransferFinished) {
                            return qsTr("The transfer is finished!")
                        } else if (bindings.systemState === Enums.AnalysisCompleted) {
                            return qsTr("Please connect a target storage...")
                        }
                    }

                    return qsTr("Unknown state (%1)").arg(bindings.systemState)
                }

                horizontalAlignment: Qt.AlignHCenter

                color: {
                    if(bindings.targetName === "") {
                        return Environment.colorWarning
                    } else {
                        // Transfer in progress...
                        if(bindings.systemState === Enums.AnalysisCompleted) {
                            return Environment.colorText
                        } else if([Enums.CopyCleanFiles, Enums.GeneratingReport].includes(bindings.systemState)) {
                            return Environment.colorText
                        } else if (bindings.systemState === Enums.GeneratingReport) {
                            return Environment.colorText
                        } else if (bindings.systemState === Enums.TransferFinished) {
                            return Environment.colorClean
                        }
                    }

                    return Environment.colorText
                }

                section: Constants.Section.Title2
            }

        }
    }

    RowLayout {
        anchors {
            top: pnlHeader.bottom
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            topMargin: 80
            bottomMargin: 80
        }

        width: parent.width/3
        height: parent.height/3

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
