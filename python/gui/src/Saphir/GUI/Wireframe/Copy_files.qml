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
            spacing: 40

            /* Title */
            ColumnLayout {
                Layout.preferredWidth: parent.width

                WfText {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Output storage: UNTITLED"
                    font.pixelSize: 24
                }

                WfText {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Copying files..."
                    font.pixelSize: 16
                }
            }

            GridLayout {
                id: grdLyt

                Layout.preferredWidth: parent.width
                Layout.fillHeight: true

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
                            visible: col === 2
                            progress: Math.random() * 100
                        }

                    }
                }

                Item {
                    Layout.fillHeight: true
                }
            }

        }
    }
}
