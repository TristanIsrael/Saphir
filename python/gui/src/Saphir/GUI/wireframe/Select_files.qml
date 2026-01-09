import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main

    WfPanel {
        id: pnl

        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            margins: height/10
        }

        WfText {
            id: lbl1

            anchors {
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: 20
            }

            text: "Support name: UNTITLED"
            font.pixelSize: 24
        }

        /*WfText {
            id: lbl2

            anchors {
                horizontalCenter: parent.horizontalCenter
                top: lbl1.bottom
                topMargin: 20
            }

            text: "Please select the files to analyze"
            font.pixelSize: 24
        }*/

        property list<string> fileNames: [ "application-gimp-gradient.icns", "application-illustrator-svg.icns", "application-illustrator.icns", "application-pdf.icns", "application-vnd.corel-draw-compressed.icns", "application-vnd.corel-draw-template.icns", "application-vnd.corel-draw.icns", "application-vnd.ms.xaml.icns", "application-vnd.wordperfect-graphic.icns", "image-svg+xml-compressed.icns", "image-svg+xml.icns", "image-vnd.dxf.icns", "image-vnd.windows-metafile.icns", "Inkscape-Generic.icns", "inkscape.icns" ]

        GridLayout {
            anchors {
                top: lbl1.bottom
                topMargin: 40
                left: parent.left
                leftMargin: 20
                right: parent.right
                rightMargin: 20
                bottom: btnOk.top
                bottomMargin: 40
            }

            columns: 4
            clip: true

            Repeater {
                model: pnl.fileNames.length*4

                Item {
                    readonly property int col: index%4
                    readonly property int row: (index-1) /4
                    Layout.preferredHeight: 40

                    WfCheckbox {
                        visible: col === 0
                        checked: Math.floor(Math.random() * 10) % 3
                    }

                    WfText {
                        visible: col === 1
                        font.family: "Material Icons"
                        text: Constants.iconFile
                        font.pixelSize: 24
                    }

                    WfText {
                        visible: col === 2
                        text: pnl.fileNames[row]
                        Layout.fillWidth: true
                    }

                    WfText {
                        visible: col === 3
                        text: (Math.random()*10).toFixed(2) +" MB"
                    }
                }
            }

            Item { Layout.fillHeight: true }
        }

        WfButton {
            id: btnOk

            anchors {
                bottom: parent.bottom
                bottomMargin: 20
                horizontalCenter: parent.horizontalCenter
            }

            label: "OK"
        }
    }
}
