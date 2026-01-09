import QtQuick
import QtQuick.Effects

Item {
    id: root

    property bool outlined: true
    property alias icon: txt.text
    property color taint: enabled ? "#d8d8d8" : "#444480"
    property int borderWidth: enabled ? 7 : 1
    property bool highlight: true

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 80
    implicitHeight: 80
    clip: false

    Circle { // Wrapper
        id: wrapper

        width: root.width// + 2*shadow.shadowBlur
        height: root.height// + 2*shadow.shadowBlur

        borderWidth: root.borderWidth
        borderColor: root.enabled ? Qt.alpha(Qt.lighter(root.taint, 2.5), 0.9) : root.taint

        MultiEffect {
            anchors.fill: parent

            source: ShaderEffectSource {
                width: root.width
                height: root.height

                sourceItem: back
                sourceRect: Qt.rect(root.x, root.y, root.width, root.height)
                hideSource: true
                live: true
            }

            anchors {
                fill: root
            }

            brightness: root.enabled ? 0.7 : 0.2
            saturation: root.enabled ? 0.1 : 0.0
            blurEnabled: true
            blurMax: 45
            blur: 0.7
            colorization: 0.3
            colorizationColor: root.taint
            autoPaddingEnabled: false
            maskEnabled: true
            maskSource: ShaderEffectSource {
                sourceItem: Circle {
                    color: "white"
                    width: root.width
                    height: root.height
                    layer.enabled: true
                    borderWidth: 0
                }
            }
        }        
    }

    MultiEffect {
        id: shadow
        source: wrapper
        anchors.fill: wrapper
        shadowEnabled: true
        shadowColor: root.enabled ? "#aaffffff" : "#aaffffff"
        shadowBlur: root.enabled ? 1.0 : 0.2
    }

    Item {
        anchors {
            centerIn: wrapper
        }

        width: wrapper.width *0.9
        height: wrapper.width *0.9

        Text {
            id: txt
            anchors.fill: parent
            font.family: outlined ? "Material Icons Outlined" : "Material Icons"
            text: Constants.iconHelp
            font.pixelSize: parent.height
            color: root.enabled ? "#aafafafa" : "black"
        }
    }
}
