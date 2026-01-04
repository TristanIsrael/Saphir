import QtQuick
import QtQuick.Controls
import QtQuick3D
import QtQuick3D.Helpers

Window {
    visible: true
    width: 1200
    height: 800
    title: "Carousel 3D - Prisme Octogonal"
    color: "#1a1a2e"

    // Image de fond
    /*Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0f0c29" }
            GradientStop { position: 0.4; color: "#302b63" }
            GradientStop { position: 0.8; color: "#24243e" }
            GradientStop { position: 1.0; color: "#1a1a2e" }
        }

        // Motif de fond décoratif
        Repeater {
            model: 50

            Rectangle {
                width: 2 + Math.random() * 3
                height: width
                radius: width / 2
                color: Qt.rgba(1, 1, 1, 0.1 + Math.random() * 0.3)
                x: Math.random() * parent.width
                y: Math.random() * parent.height

                NumberAnimation on opacity {
                    from: 0.2
                    to: 1.0
                    duration: 2000 + Math.random() * 2000
                    loops: Animation.Infinite
                    running: true
                }
            }
        }
    }*/

    Image {
        anchors.fill: parent
        source: "qrc:/qt/qml/TestCarousel3D/back.jpg"
        fillMode: Image.PreserveAspectCrop
    }

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            clearColor: "transparent"
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 900)
            eulerRotation.x: 0
            clipFar: 5000
            clipNear: 1
        }

        DirectionalLight {
            eulerRotation.x: -15
            eulerRotation.y: 0
            brightness: 1.5
            ambientColor: Qt.rgba(0.4, 0.4, 0.4, 1.0)
        }

        DirectionalLight {
            eulerRotation.x: 15
            eulerRotation.y: 180
            brightness: 0.4
            ambientColor: Qt.rgba(0.2, 0.2, 0.2, 1.0)
        }

        PointLight {
            position: Qt.vector3d(0, 0, 800)
            brightness: 0.8
            ambientColor: Qt.rgba(0.3, 0.3, 0.3, 1.0)
        }

        Node {
            id: prismRoot

            property real rotationAngle: 0
            property int currentFace: 0

            Behavior on rotationAngle {
                NumberAnimation {
                    duration: 800
                    easing.type: Easing.InOutCubic
                }
            }

            eulerRotation.y: rotationAngle

            NumberAnimation on rotationAngle {
                id: rotationAnimation
                from: rotationAngle
                to: rotationAngle + 360
                duration: 24000
                loops: Animation.Infinite
                running: false

                onFinished: {
                    if (running) {
                        from = 0
                        to = 360
                        restart()
                    }
                }
            }

            function goToFace(faceIndex) {
                rotationAnimation.running = false
                currentFace = faceIndex
                rotationAngle = -faceIndex * 45
            }

            Repeater3D {
                model: [
                    { angle: 0, title: "Profil Utilisateur", icon: "👤", color1: "#e74c3c", color2: "#c0392b", subtitle: "Informations personnelles" },
                    { angle: 45, title: "Statistiques", icon: "📊", color1: "#3498db", color2: "#2980b9", subtitle: "Analyses et rapports" },
                    { angle: 90, title: "Messages", icon: "✉️", color1: "#2ecc71", color2: "#27ae60", subtitle: "Boîte de réception" },
                    { angle: 135, title: "Paramètres", icon: "⚙️", color1: "#f39c12", color2: "#d68910", subtitle: "Configuration" },
                    { angle: 180, title: "Notifications", icon: "🔔", color1: "#9b59b6", color2: "#8e44ad", subtitle: "Alertes et rappels" },
                    { angle: 225, title: "Galerie", icon: "🖼️", color1: "#1abc9c", color2: "#16a085", subtitle: "Photos et médias" },
                    { angle: 270, title: "Calendrier", icon: "📅", color1: "#e67e22", color2: "#d35400", subtitle: "Événements à venir" },
                    { angle: 315, title: "Contacts", icon: "📞", color1: "#34495e", color2: "#2c3e50", subtitle: "Liste de contacts" }
                ]

                Node {
                    property var panelData: modelData
                    property real radius: 550
                    property real radians: panelData.angle * Math.PI / 180

                    // Calculer si cette face est visible (face active ou adjacentes)
                    property int faceOffset: {
                        var diff = (index - prismRoot.currentFace + 8) % 8
                        if (diff > 4) diff = diff - 8
                        return diff
                    }
                    property bool isActive: faceOffset === 0
                    property bool isAdjacent: Math.abs(faceOffset) === 1
                    property bool isVisible: isActive || isAdjacent

                    visible: isVisible

                    position: Qt.vector3d(
                        radius * Math.sin(radians),
                        0,
                        radius * Math.cos(radians)
                    )

                    eulerRotation: Qt.vector3d(0, panelData.angle, 0)

                    Model {
                        source: "#Rectangle"
                        scale: isActive ? Qt.vector3d(3.7, 2.35, 0.1) : Qt.vector3d(3.5, 2.2, 0.1)

                        Behavior on scale {
                            Vector3dAnimation {
                                duration: 600
                                easing.type: Easing.OutBack
                            }
                        }

                        materials: PrincipledMaterial {
                            alphaMode: PrincipledMaterial.Blend
                            metalness: isActive ? 0.2 : 0.5
                            roughness: isActive ? 0.6 : 0.4
                            opacity: isActive ? 0.88 : 0.65

                            Behavior on opacity {
                                NumberAnimation { duration: 600 }
                            }

                            Behavior on metalness {
                                NumberAnimation { duration: 600 }
                            }

                            Behavior on roughness {
                                NumberAnimation { duration: 600 }
                            }

                            baseColorMap: Texture {
                                sourceItem: Rectangle {
                                    width: 800
                                    height: 500

                                    gradient: Gradient {
                                        GradientStop { position: 0.0; color: panelData.color1 }
                                        GradientStop { position: 1.0; color: panelData.color2 }
                                    }

                                    radius: 20
                                    border.color: isActive ? "#FFD700" : Qt.rgba(1, 1, 1, 0.5)
                                    border.width: isActive ? 5 : 3

                                    opacity: isActive ? 0.92 : 0.7

                                    Behavior on opacity {
                                        NumberAnimation { duration: 600 }
                                    }

                                    // Effet verre dépoli plus visible
                                    Rectangle {
                                        anchors.fill: parent
                                        radius: parent.radius
                                        opacity: isActive ? 0.08 : 0.18
                                        color: "white"
                                    }

                                    // Pattern de points pour simuler le givrage
                                    Repeater {
                                        model: isActive ? 30 : 50
                                        Rectangle {
                                            width: isActive ? 4 : 6
                                            height: width
                                            radius: width / 2
                                            color: Qt.rgba(1, 1, 1, isActive ? 0.15 : 0.25)
                                            x: (index * 137.5) % parent.width
                                            y: (index * 217.3) % parent.height
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: 2
                                        radius: parent.radius - 2
                                        opacity: isActive ? 0.05 : 0.12
                                        gradient: Gradient {
                                            orientation: Gradient.Horizontal
                                            GradientStop { position: 0.0; color: "transparent" }
                                            GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.4) }
                                            GradientStop { position: 1.0; color: "transparent" }
                                        }
                                    }

                                    // Effet de verre subtil sur toutes les faces
                                    Rectangle {
                                        anchors.fill: parent
                                        radius: parent.radius
                                        gradient: Gradient {
                                            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, isActive ? 0.08 : 0.15) }
                                            GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, isActive ? 0.03 : 0.05) }
                                            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, isActive ? 0.08 : 0.15) }
                                        }
                                    }

                                    // Reflet de verre
                                    Rectangle {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        radius: parent.radius - 4
                                        border.color: Qt.rgba(1, 1, 1, isActive ? 0.2 : 0.3)
                                        border.width: 1
                                        color: "transparent"
                                    }

                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 25

                                        Row {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            spacing: 40

                                            Rectangle {
                                                width: 100
                                                height: 100
                                                radius: 50
                                                color: Qt.rgba(1, 1, 1, 0.2)
                                                border.color: "white"
                                                border.width: 3

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: panelData.icon
                                                    font.pixelSize: 60
                                                }
                                            }

                                            Column {
                                                spacing: 8
                                                anchors.verticalCenter: parent.verticalCenter

                                                Text {
                                                    text: panelData.title
                                                    font.pixelSize: 38
                                                    font.bold: true
                                                    color: "white"
                                                }

                                                Text {
                                                    text: panelData.subtitle
                                                    font.pixelSize: 18
                                                    color: Qt.rgba(1, 1, 1, 0.8)
                                                }
                                            }
                                        }

                                        Rectangle {
                                            width: 650
                                            height: 2
                                            radius: 1
                                            color: Qt.rgba(1, 1, 1, 0.4)
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }

                                        Row {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            spacing: 30

                                            Column {
                                                spacing: 12

                                                Repeater {
                                                    model: 3
                                                    Row {
                                                        spacing: 10

                                                        Rectangle {
                                                            width: 70
                                                            height: 50
                                                            radius: 8
                                                            color: Qt.rgba(1, 1, 1, 0.25)
                                                            border.color: "white"
                                                            border.width: 2

                                                            Text {
                                                                anchors.centerIn: parent
                                                                text: (index + 1) * 24
                                                                font.pixelSize: 20
                                                                font.bold: true
                                                                color: "white"
                                                            }
                                                        }

                                                        Rectangle {
                                                            width: 150
                                                            height: 50
                                                            radius: 8
                                                            color: Qt.rgba(1, 1, 1, 0.15)

                                                            Column {
                                                                anchors.centerIn: parent
                                                                spacing: 2

                                                                Text {
                                                                    text: ["Actifs", "En cours", "Complétés"][index]
                                                                    font.pixelSize: 14
                                                                    color: "white"
                                                                }

                                                                Rectangle {
                                                                    width: 130
                                                                    height: 6
                                                                    radius: 3
                                                                    color: Qt.rgba(1, 1, 1, 0.3)

                                                                    Rectangle {
                                                                        width: parent.width * (0.4 + index * 0.25)
                                                                        height: parent.height
                                                                        radius: parent.radius
                                                                        color: "white"
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }

                                            Column {
                                                spacing: 15

                                                Rectangle {
                                                    width: 200
                                                    height: 60
                                                    radius: 30
                                                    color: Qt.rgba(1, 1, 1, 0.3)
                                                    border.color: "white"
                                                    border.width: 3

                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "Accéder ▶"
                                                        font.pixelSize: 20
                                                        font.bold: true
                                                        color: "white"
                                                    }
                                                }

                                                Row {
                                                    anchors.horizontalCenter: parent.horizontalCenter
                                                    spacing: 10

                                                    Repeater {
                                                        model: 3
                                                        Rectangle {
                                                            width: 55
                                                            height: 55
                                                            radius: 10
                                                            color: Qt.rgba(1, 1, 1, 0.2)
                                                            border.color: Qt.rgba(1, 1, 1, 0.5)
                                                            border.width: 2

                                                            Text {
                                                                anchors.centerIn: parent
                                                                text: ["⚡", "📈", "💡"][index]
                                                                font.pixelSize: 28
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        Row {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            spacing: 15

                                            Repeater {
                                                model: 8
                                                Rectangle {
                                                    width: index === prismRoot.currentFace ? 14 : 10
                                                    height: width
                                                    radius: width / 2
                                                    color: index === prismRoot.currentFace ? "#FFD700" : Qt.rgba(1, 1, 1, 0.3)
                                                    border.color: index === prismRoot.currentFace ? "white" : "transparent"
                                                    border.width: 2

                                                    Behavior on width {
                                                        NumberAnimation { duration: 300 }
                                                    }

                                                    Behavior on color {
                                                        ColorAnimation { duration: 300 }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(6.5, 0.08, 6.5)
                y: 120
                materials: PrincipledMaterial {
                    baseColor: Qt.rgba(1, 1, 1, 0.12)
                    metalness: 0.8
                    roughness: 0.2
                }
            }

            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(6.5, 0.08, 6.5)
                y: -120
                materials: PrincipledMaterial {
                    baseColor: Qt.rgba(1, 1, 1, 0.12)
                    metalness: 0.8
                    roughness: 0.2
                }
            }
        }
    }

    Rectangle {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 30
        width: 650
        height: 130
        color: Qt.rgba(0, 0, 0, 0.85)
        radius: 15
        border.color: "#3498db"
        border.width: 3

        Column {
            anchors.centerIn: parent
            spacing: 18

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "🎡 Carousel 3D - Prisme Octogonal"
                font.pixelSize: 28
                font.bold: true
                color: "white"
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 12

                Button {
                    width: 120
                    height: 45
                    text: rotationAnimation.running ? "⏸ Pause" : "▶ Auto"

                    background: Rectangle {
                        color: parent.pressed ? "#c0392b" : (parent.hovered ? "#e74c3c" : "#d35400")
                        radius: 10
                        border.color: parent.hovered ? "white" : "transparent"
                        border.width: 2
                    }

                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        if (rotationAnimation.running) {
                            rotationAnimation.running = false
                        } else {
                            rotationAnimation.from = prismRoot.rotationAngle
                            rotationAnimation.to = prismRoot.rotationAngle + 360
                            rotationAnimation.running = true
                        }
                    }
                }

                Button {
                    width: 120
                    height: 45
                    text: "◀ Face"

                    background: Rectangle {
                        color: parent.pressed ? "#2980b9" : (parent.hovered ? "#3498db" : "#2c3e50")
                        radius: 10
                        border.color: parent.hovered ? "white" : "transparent"
                        border.width: 2
                    }

                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        var newFace = (prismRoot.currentFace - 1 + 8) % 8
                        prismRoot.goToFace(newFace)
                    }
                }

                Button {
                    width: 120
                    height: 45
                    text: "Face ▶"

                    background: Rectangle {
                        color: parent.pressed ? "#2980b9" : (parent.hovered ? "#3498db" : "#2c3e50")
                        radius: 10
                        border.color: parent.hovered ? "white" : "transparent"
                        border.width: 2
                    }

                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        var newFace = (prismRoot.currentFace + 1) % 8
                        prismRoot.goToFace(newFace)
                    }
                }

                Button {
                    width: 120
                    height: 45
                    text: rotationAnimation.duration === 24000 ? "⚡ Rapide" : "🐌 Normal"

                    background: Rectangle {
                        color: parent.pressed ? "#27ae60" : (parent.hovered ? "#2ecc71" : "#16a085")
                        radius: 10
                        border.color: parent.hovered ? "white" : "transparent"
                        border.width: 2
                    }

                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.bold: true
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: {
                        rotationAnimation.duration = rotationAnimation.duration === 24000 ? 10000 : 24000
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 30
        width: 550
        height: 70
        color: Qt.rgba(0, 0, 0, 0.75)
        radius: 12

        Column {
            anchors.centerIn: parent
            spacing: 5

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "🎨 Face " + (prismRoot.currentFace + 1) + "/8 : " +
                      ["Profil", "Statistiques", "Messages", "Paramètres", "Notifications", "Galerie", "Calendrier", "Contacts"][prismRoot.currentFace]
                font.pixelSize: 18
                color: "#ecf0f1"
                font.bold: true
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Naviguez avec les boutons ◀ et ▶"
                font.pixelSize: 14
                color: Qt.rgba(1, 1, 1, 0.7)
            }
        }
    }
}
