import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import QtQuick.Layouts
import QtQuick.Effects
import Qt5Compat.GraphicalEffects
import Components

Item {
    id: root

    property alias lines: lines
    property alias maHour: maHour
    property alias lblTime: lblTime
    property alias gradientRect: gradientRect
    property alias gradientStart: gradientStart
    property alias gradientStop: gradientStop

    height: implicitHeight
    width: implicitWidth
    implicitHeight: 40
    implicitWidth: 800

    Rectangle {
        // Wrapper
        id: wrapper

        anchors.fill: parent
        visible: true
        radius: height
        color: bindings.systemStateColor
        border {
            width: 1
            color: "#e8e8e8"
        }

        MultiEffect {
            anchors.fill: parent
            visible: true

            source: ShaderEffectSource {
                width: wrapper.width
                height: wrapper.height

                sourceItem: back
                sourceRect: Qt.rect(wrapper.x, wrapper.y, wrapper.width,
                                    wrapper.height)
                hideSource: true
                live: true
            }

            anchors {
                fill: wrapper
            }

            brightness: 0.2
            saturation: 0.0
            blurEnabled: true
            blurMax: 45
            blur: 0.7
            colorization: 0.3
            colorizationColor: "#d8d8d8"
            autoPaddingEnabled: false
            maskEnabled: true
            maskSource: ShaderEffectSource {
                sourceItem: Rectangle {
                    color: "white"
                    width: wrapper.width
                    height: wrapper.height
                    layer.enabled: true
                }
            }
        }
    }

    // Logo
    RowLayout {
        id: lytLogo

        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: root.height * 0.1
        }

        height: root.height - anchors.topMargin

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
        visible: false

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
        visible: true

        gradient: Gradient {
            GradientStop {
                id: gradientStart
                position: 0.0
                //color: Qt.alpha(systemStateColor, 0.1)
            }
            GradientStop {
                id: gradientStop
                position: 1.0
                //color: Qt.alpha(systemStateColor, 0.3)
            }
        }

        layer.enabled: true
        layer.smooth: true
    }

    // Left information
    RowLayout {
        anchors {
            top: parent.top
            topMargin: root.height * 0.1
            left: parent.left
            leftMargin: root.height * 0.2 * (Environment.mainWidth / Environment.mainHeight)
            bottom: parent.bottom
            bottomMargin: root.height * 0.1
        }

        //height: root.height - anchors.topMargin
        width: lytLogo.x - x

        Text {
            id: lblTime
            color: "#fffdfafd"
            text: "HH:mm:ss Z"
            font.pixelSize: parent.height * 0.7

            MouseArea {
                id: maHour
                anchors.fill: parent
            }
        }

        Label {
            id: restriction

            text: qsTr("Restricted")
            font.capitalization: Font.AllUppercase
            font.pixelSize: parent.height * 0.5
            color: "#90fcf8"
        }
    }

    // Right icons
    RowLayout {
        anchors {
            top: parent.top
            topMargin: root.height * 0.1
            right: parent.right
            rightMargin: root.height * 0.1 * (Environment.mainWidth / Environment.mainHeight)
            bottom: parent.bottom
            bottomMargin: root.height * 0.1
        }

        //width: root.width - lytLogo.width - lytLogo.x
        layoutDirection: Qt.RightToLeft

        Energy {
            color: "#fafafa"
        }
    }

    Bindings {
        id: bindings
    }
}
