import QtQuick
import QtQuick.Shapes
import QtQuick.Layouts
import Components

Item {
    id: root

    property int percent: (bindings.nbFinished / bindings.queueSize)*100
    property real stepPercent: 2.5
    property int totalSteps: Math.ceil(100 / stepPercent)
    property int remainingTimeInMinutes: bindings.remainingTimeInMinutes

    width: implicitWidth
    height: implicitHeight
    implicitWidth: 400
    implicitHeight: 400

    property color filledColor: Environment.colorClear
    property color emptyColor: "#44777777"

    property real radius: Math.min(width, height)/2 - 10
    property real thickness: 30
    property real cx: width/2
    property real cy: height/2

    // --- Repeater pour créer toutes les sections ---
    Repeater {
        model: totalSteps

        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer

            ShapePath {
                strokeWidth: root.thickness
                capStyle: ShapePath.FlatCap

                // Sections remplies
                strokeColor: index < Math.round(root.percent / root.stepPercent)
                             ? root.filledColor
                             : root.emptyColor

                PathAngleArc {
                    centerX: root.cx
                    centerY: root.cy
                    radiusX: root.radius
                    radiusY: root.radius
                    startAngle: -90 + index * 360 / root.totalSteps
                    sweepAngle: 360 / root.totalSteps - 1   // -1 pour espacement entre sections
                }
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
            text: root.percent +" %"
            font.pixelSize: parent.height * 0.15
            font.bold: true
            fontSizeMode: Text.HorizontalFit
            color: Environment.colorText
        }

        Text {
            Layout.maximumWidth: root.width - root.thickness*2
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("ETA: %1 mn").arg(root.remainingTimeInMinutes)
            font.pixelSize: parent.height * 0.1
            color: Environment.colorText
        }

        Item { Layout.fillHeight: true }
    }

    Bindings {
        id: bindings
    }

}
