import QtQuick
import QtQuick.Shapes
import QtQuick.Layouts
import Components

Item {
    id: root

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 400
    implicitHeight: 400

    property int total: bindings.nbClean + bindings.nbInfected + bindings.nbWaiting

    property real radius: Math.min(width, height)/2 - 10
    property real thickness: 30
    property real cx: width/2
    property real cy: height/2

    // --- Section 1 : Clean ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: Environment.colorClean
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90
                sweepAngle: 360 * bindings.nbClean / root.total
            }
        }
    }

    // --- Section 2 : Infected ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: Environment.colorInfected
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90 + 360 * bindings.nbClean / root.total
                sweepAngle: 360 * bindings.nbInfected / root.total
            }
        }
    }

    // --- Section 3 : Waiting ---
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: thickness
            strokeColor: Environment.colorWaiting
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.cx
                centerY: root.cy
                radiusX: root.radius
                radiusY: root.radius
                startAngle: -90 + 360 * (bindings.nbClean + bindings.nbInfected) / root.total
                sweepAngle: 360 * bindings.nbWaiting / root.total
            }
        }
    }

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
            color: Environment.colorText
        }

        Text {
            Layout.maximumWidth: root.width - root.thickness*2
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Files")
            font.pixelSize: parent.height * 0.1
            font.capitalization: Font.AllUppercase
            color: Environment.colorText
        }

        Item { Layout.fillHeight: true }
    }

    Bindings {
        id: bindings
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
