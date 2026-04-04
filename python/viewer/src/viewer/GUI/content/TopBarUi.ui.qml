import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import QtQuick.Layouts
import QtQuick.Effects
import Qt5Compat.GraphicalEffects
import Components

Item {
    id: root

    property alias maHour: maHour
    property alias lblTime: lblTime
    property alias lblTitle: lblTitle

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

            brightness: 0.0
            saturation: 0.0
            blurEnabled: true
            blurMax: 45
            blur: 0.7
            colorization: 0.3
            colorizationColor: bindings.systemStateColor
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
            topMargin: root.height * 0.05
            bottom: parent.bottom
            bottomMargin: root.height * 0.05
        }

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

            MultiEffect {
                visible: Environment.logoBrightness != 0.0
                anchors.fill: imgLogo
                source: imgLogo 
                brightness: Environment.logoBrightness
            }
        }

        Text {
            Layout.alignment: Qt.AlignVCenter
            text: "SAPHIR"
            font.family: "LED Dot-Matrix"
            font.pixelSize: parent.height * 0.8
            color: Environment.colorText
        }

        Item {
            Layout.fillWidth: true
        }
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

        StyledText {
            id: lblTime
            color: Environment.colorText
            text: "HH:mm:ss Z"
            font.pixelSize: parent.height * 0.7

            MouseArea {
                id: maHour
                anchors.fill: parent
            }
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
        spacing: 5

        Energy {}

        Brightness {
            visible: bindings.ambientLightSensorReady
        }

        Item {}

        StyledText {
            id: lblTitle

            text: qsTr("Viewer")
            font.capitalization: Font.AllUppercase
            font.pixelSize: parent.height * 0.5
            font.bold: true
        }
    }

    Bindings {
        id: bindings
    }
}
