import QtQuick 2.15
import Qt5Compat.GraphicalEffects

Rectangle {
    id: root

    // Propriétés personnalisables
    property real borderRadius: height/12
    property color glassColor: "#30ffffff"
    property real blurRadius: 32
    property real borderWidth: 1
    property color borderColor: "#60ffffff"
    property Item backgroundSource: parent
    property bool shadow: true
    property bool highlight: true
    property real brightness: 0.15
    property real contrast: 0.1

    // Le contenu à afficher sur le verre
    default property alias content: contentItem.data

    color: "transparent"
    radius: borderRadius
    clip: true

    // Capturer l'arrière-plan
    ShaderEffectSource {
        id: effectSource
        anchors.fill: parent
        sourceItem: root.backgroundSource
        sourceRect: Qt.rect(root.x, root.y, root.width, root.height)
        visible: false
        live: true
        recursive: false
    }

    // Rectangle principal avec coins arrondis
    Rectangle {
        id: glassRect
        anchors.fill: parent
        radius: root.borderRadius
        color: "transparent"

        Item {
            anchors.fill: parent

            // Arrière-plan flouté
            FastBlur {
                id: blurredBg
                anchors.fill: parent
                source: effectSource
                radius: root.blurRadius
                visible: false
            }

            BrightnessContrast {
                id: brightenedBg
                anchors.fill: parent
                source: blurredBg
                brightness: root.brightness
                contrast: root.contrast
                visible: false
            }

            OpacityMask {
                anchors.fill: parent
                source: brightenedBg
                maskSource: Rectangle {
                    width: glassRect.width
                    height: glassRect.height
                    radius: glassRect.radius
                }
            }
        }

        // Overlay coloré semi-transparent avec highlight
        Rectangle {
            anchors.fill: parent
            radius: root.borderRadius
            visible: root.highlight

            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.rgba(glassColor.r, glassColor.g, glassColor.b, 0.0) } // ~7 %
                GradientStop { position: 0.7; color: Qt.rgba(glassColor.r, glassColor.g, glassColor.b, 0.13) }
                GradientStop { position: 1.0; color: Qt.rgba(glassColor.r, glassColor.g, glassColor.b, 0.27) }
            }
        }

        // Overlay coloré semi-transparent sans highlight
        Rectangle {
            anchors.fill: parent
            radius: root.borderRadius
            visible: !root.highlight
            color: root.glassColor
        }

        // Reflet lumineux principal diagonal
        Rectangle {
            width: Math.sqrt(parent.width * parent.width + parent.height * parent.height) * 1.2
            height: 40
            anchors.centerIn: parent
            rotation: -45
            opacity: 0.1
            visible: false

            gradient: Gradient {
                orientation: Gradient.Vertical
                GradientStop { position: 0.0; color: "transparent" }
                GradientStop { position: 0.2; color: "#20ffffff" }
                GradientStop { position: 0.4; color: "#66ffffff" }
                GradientStop { position: 0.6; color: "#66ffffff" }
                GradientStop { position: 0.8; color: "#20ffffff" }
                GradientStop { position: 1.0; color: "transparent" }
            }
        }


        // Bordure
        Rectangle {
            anchors.fill: parent
            radius: root.borderRadius
            color: "transparent"
            border.width: root.borderWidth
            border.color: root.borderColor
        }

        // shadow interne (bas-droite)
        Rectangle {
            anchors.fill: parent
            visible: root.shadow
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#00000000" }
                GradientStop { position: 1.0; color: "#10000000" }
            }
        }
    }

    // Reflet inférieur droit
    /*Item {
        width: parent.width/3
        height: width

        anchors {
            right: parent.right
            bottom: parent.bottom
        }

        RadialGradient {
            anchors.fill: parent
            horizontalOffset: width/2
            verticalOffset: height/2
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#ccffffff" }
                GradientStop { position: 0.56; color: "#00ffffff" }
            }
        }
    }*/

    // Conteneur pour le contenu personnalisé
    Item {
        id: contentItem
        anchors.fill: parent
        anchors.margins: 10
    }
}
