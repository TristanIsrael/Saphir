import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components

Item {
    id: root

    property alias lines: lines
    property alias maHour: maHour
    property alias lblTime: lblTime
    property alias gradientRect: gradientRect

    height: implicitHeight
    width: implicitWidth
    implicitHeight: 100
    implicitWidth: 800

    Rectangle {
        id: backg
        anchors.fill: parent
        color: "#050910"
        visible: false
    }

    // Logo
    RowLayout {
        id: lytLogo

        height: parent.height * 0.8
        //width: parent.width
        anchors.centerIn: parent
        spacing: 0

        Item {
            Layout.fillWidth: true
        }

        Item {
            Layout.preferredWidth: height
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignVCenter

            Image {
                id: imgLogo
                anchors.fill: parent
                source: "images/Logo.png"
                fillMode: Image.PreserveAspectFit
                antialiasing: true
            }
        }

        Text {
            Layout.alignment: Qt.AlignVCenter
            text: "SAPHIR"
            font.family: "LED Dot-Matrix"
            font.pixelSize: parent.height * 0.8
            color: "#fafdfa"
        }

        Item {
            Layout.fillWidth: true
        }
    }

    // Decoration
    Item {
        id: lines
        anchors.fill: parent
        visible: true

        property int strokeWidth: 2

        Shape {
            anchors.fill: parent

            ShapePath {
                strokeWidth: lines.strokeWidth
                strokeColor: "#442a8dc5"
                fillColor: "transparent"
                joinStyle: ShapePath.RoundJoin
                capStyle: ShapePath.RoundCap

                PathPolyline {
                    path: [Qt.point(root.width * 0.07,
                                    root.height * 0.4), Qt.point(
                            root.width * 0.35, root.height * 0.4), Qt.point(
                            root.width * 0.38,
                            root.height), Qt.point(root.width * 0.62, root.height), Qt.point(
                            root.width * 0.65,
                            root.height * 0.4), Qt.point(root.width * 0.93,
                                                         root.height * 0.4)]
                }

                PathPolyline {
                    path: [Qt.point(root.width * 0.07,
                                    root.height * 0.9), Qt.point(
                            root.width * 0.25, root.height * 0.9)]
                }

                PathPolyline {
                    path: [Qt.point(root.width * 0.93,
                                    root.height * 0.9), Qt.point(
                            root.width * 0.75, root.height * 0.9)]
                }
            }
        }

        HalfCircle {
            x: root.width * 0.07 - width - strokeWidth
            y: root.height * 0.4
            height: root.height * 0.9 - y
            width: root.height * 0.9 - y
            clockwise: false
            strokeWidth: lines.strokeWidth
        }

        HalfCircle {
            x: root.width * 0.93 + strokeWidth
            y: root.height * 0.4
            height: root.height * 0.9 - y
            width: root.height * 0.9 - y
            clockwise: true
            strokeWidth: lines.strokeWidth
        }

        layer.enabled: true
        layer.smooth: true
        layer.samplerName: "maskSource"
    }

    Rectangle {
        id: gradientRect
        anchors.fill: parent
        visible: false

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: "#66345878"
            }
            GradientStop {
                position: 1.0
                color: "#cc4096c7"
            }
        }

        layer.enabled: true
        layer.smooth: true
    }

    // Left information
    RowLayout {
        y: root.height * 0.4
        x: root.width * 0.07
        height: root.height * 0.5
        width: lytLogo.x - x

        Label {
            id: lblTime
            color: "#fffdfafd"
            text: "HH:mm:ss Z"
            font.pixelSize: parent.height * 0.5

            MouseArea {
                id: maHour
                anchors.fill: parent
            }
        }

        Label {
            id: restriction

            text: qsTr("Restricted")
            font.capitalization: Font.AllUppercase
            font.pixelSize: parent.height * 0.4
            color: "#90fcf8"
        }
    }

    // Right icons
    RowLayout {
        y: root.height * 0.4
        x: root.width - width - (root.width * 0.07) - (root.height * 0.9 * 0.1)
        height: root.height * 0.5
        width: root.width - lytLogo.width - lytLogo.x

        layoutDirection: Qt.RightToLeft

        Energy {
            color: "#fafafa"
        }
    }
}
