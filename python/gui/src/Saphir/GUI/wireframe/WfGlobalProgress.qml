import QtQuick
import QtQuick.Shapes
import QtQuick.Layouts

Item {
    id: root

    property int nbClean: 1013
    property int nbInfected: 5012
    property int nbWaiting: 10120

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 400
    implicitHeight: 400

    property int total: nbClean + nbInfected + nbWaiting

    property color colorClean: "#4CAF50"
    property color colorInfected: "#F44336"
    property color colorWaiting: "#FF9800"

    property real radius: Math.min(width, height)/2 - 10
    property real thickness: 30
    property real cx: width/2
    property real cy: height/2

    // --- Section 1 : Clean ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: root.colorClean
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90
                sweepAngle: 360 * root.nbClean / root.total
            }
        }
    }

    // --- Section 2 : Infected ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: root.colorInfected
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90 + 360 * root.nbClean / root.total
                sweepAngle: 360 * root.nbInfected / root.total
            }
        }
    }

    // --- Section 3 : Waiting ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: root.colorWaiting
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90 + 360 * (root.nbClean + root.nbInfected) / root.total
                sweepAngle: 360 * root.nbWaiting / root.total
            }
        }
    }

    // --- Labels centrés dans chaque section ---
    /*Text {
        visible: root.nbClean > 0
        text: root.nbClean
        font.bold: true
        font.pixelSize: Math.min(root.width, root.height) * 0.07
        anchors.centerIn: undefined
        x: radialPosition(-90, 360*root.nbClean/root.total).x - width/2
        y: radialPosition(-90, 360*root.nbClean/root.total).y - height/2
    }

    Text {
        visible: root.nbInfected > 0
        text: root.nbInfected
        font.bold: true
        font.pixelSize: Math.min(root.width, root.height) * 0.07
        anchors.centerIn: undefined
        x: radialPosition(-90 + 360*root.nbClean/root.total,
                          360*root.nbInfected/root.total).x - width/2
        y: radialPosition(-90 + 360*root.nbClean/root.total,
                          360*root.nbInfected/root.total).y - height/2
    }

    Text {
        visible: root.nbWaiting > 0
        text: root.nbWaiting
        font.bold: true
        font.pixelSize: Math.min(root.width, root.height) * 0.07
        anchors.centerIn: undefined
        x: radialPosition(-90 + 360*(root.nbClean+root.nbInfected)/root.total,
                          360*root.nbWaiting/root.total).x - width/2
        y: radialPosition(-90 + 360*(root.nbClean+root.nbInfected)/root.total,
                          360*root.nbWaiting/root.total).y - height/2
    }*/

    ColumnLayout {
        anchors{
            fill: parent
            margins: parent.width * 0.1
        }
        spacing: 0

        Item { Layout.fillHeight: true }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: root.width - root.thickness*2
            Layout.alignment: Qt.AlignHCenter
            horizontalAlignment: Text.AlignHCenter
            text: root.total
            font.pixelSize: parent.height * 0.25
            font.bold: true
            fontSizeMode: Text.HorizontalFit
        }

        Text {
            Layout.maximumWidth: root.width - root.thickness*2
            Layout.alignment: Qt.AlignHCenter
            text: "Files"
            font.pixelSize: parent.height * 0.1
            font.capitalization: Font.AllUppercase
        }

        Item { Layout.fillHeight: true }
    }

    // --- Fonction utilitaire pour position radial à l'intérieur de l'anneau ---
    function radialPosition(startAngle, sweepAngle) {
        var midAngle = startAngle + sweepAngle/2
        var rad = midAngle * Math.PI / 180
        // Position centrée dans l'anneau
        var r = root.radius - root.thickness/2 - 15 // marge 5px vers le centre
        return { x: root.cx + r * Math.cos(rad),
                 y: root.cy + r * Math.sin(rad) }
    }

}
