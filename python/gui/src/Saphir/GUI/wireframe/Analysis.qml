import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main

    property bool running: false

    WfPanel {
        id: pnl

        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            margins: height/10
        }

        discreet: true

        ColumnLayout  {
            id: colLyt
            anchors.fill: parent
            spacing: 20

            /* Progress */
            RowLayout {
                Layout.fillHeight: true
                Layout.fillWidth: true
                spacing: height/20

                Item { Layout.fillWidth: true }

                WfFilesProgress {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                }

                Item { Layout.fillWidth: true }

                WfGlobalProgress {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                }

                Item { Layout.fillWidth: true }
            }

            GridLayout {
                id: grdLyt

                //Layout.fillWidth: true
                Layout.preferredWidth: parent.width
                Layout.maximumHeight: parent.height * 0.5

                /* Files status */
                property list<string> fileNames: [ "application-gimp-gradient.icns", "application-illustrator-svg.icns", "application-illustrator.icns", "application-pdf.icns", "application-vnd.corel-draw-compressed.icns", "application-vnd.corel-draw-template.icns", "application-vnd.corel-draw.icns", "application-vnd.ms.xaml.icns", "application-vnd.wordperfect-graphic.icns", "image-svg+xml-compressed.icns", "image-svg+xml.icns", "image-vnd.dxf.icns", "image-vnd.windows-metafile.icns", "Inkscape-Generic.icns", "inkscape.icns" ]

                columns: 3
                clip: true

                Repeater {
                    model: parent.fileNames.length*3

                    Item {
                        id: itm

                        readonly property int col: index%3
                        readonly property int row: (index-1) /3
                        Layout.preferredHeight: 20

                        WfText {
                            visible: col === 0
                            font.family: "Material Icons"
                            text: Constants.iconFile
                            font.pixelSize: 24
                        }

                        WfText {
                            visible: col === 1
                            text: grdLyt.fileNames[row]
                            Layout.fillWidth: true
                        }

                        WfProgress {
                            visible: col === 2 && (row % 3 === 0)
                            progress: Math.random() * 100
                        }

                        WfText {
                            visible: col === 2 && (row % 3 > 0)
                            text: "Infected"
                        }
                    }
                }

            }
        }
    }
}
