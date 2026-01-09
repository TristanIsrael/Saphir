import QtQuick
import QtQuick.Shapes

Shape {
    id: root

    property alias color: path.fillColor
    property alias borderColor: path.strokeColor
    property alias borderWidth: path.strokeWidth

    width: 100
    height: 100

    layer.enabled: true
    layer.smooth: true    

    ShapePath {
        id: path
        fillColor: "red"
        startX: width / 2
        strokeWidth: 2
        strokeColor: "black"

        PathArc {
            x: width / 2
            y: height
            radiusX: width / 2
            radiusY: height / 2
            direction: PathArc.Clockwise
        }

        PathArc {
            x: width / 2
            y: 0
            radiusX: width / 2
            radiusY: height / 2
            direction: PathArc.Clockwise
        }
    }
}
