import QtQuick
import QtQuick.Controls
import QtQuick.Shapes
import Qt5Compat.GraphicalEffects

Rectangle {
    id: root

    property alias loadIndicator: loadIndicator
    property alias bkg: bkg
    property alias topLeft: topLeft
    property alias bottomRight: bottomRight
    property alias subTitle: subTitle
    property alias shadow: shadow

    width: 1920
    height: 1080
    color: Constants.backgroundColor

    Rectangle {
        id: bkg
        anchors.centerIn: parent
        width: parent.width / 3
        height: width / 2.7
        color: Constants.contrastColor
        radius: height * 0.35
        antialiasing: true
    }

    DropShadow {
        id: shadow
        anchors.fill: bkg
        color: Constants.contrastColor
        radius: bkg.radius / 4
        source: bkg
    }

    Text {
        anchors {
            fill: bkg
            margins: width * 0.1
        }
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font {
            family: "freshbot"
            pixelSize: width //* 0.8
        }
        fontSizeMode: Text.Fit
        text: "Panoptiscan"
        color: Constants.intermediateColor
    }

    Shape {
        id: topLeft

        x: bkg.x
        y: bkg.y
        antialiasing: true

        ShapePath {
            fillColor: "transparent"
            strokeColor: Constants.intermediateColor
            strokeWidth: 15

            PathAngleArc {
                centerX: bkg.radius
                centerY: bkg.radius
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 180
                sweepAngle: 90
            }
        }
    }


    /*Shape {
        id: tmp

        x: bkg.x + bkg.width - bkg.radius
        y: bkg.y + bkg.radius
        antialiasing: true

        ShapePath {
            fillColor: "transparent"
            strokeColor: Constants.intermediateColor
            strokeWidth: 15

            PathAngleArc {
                centerX: bkg.radius
                centerY: bkg.radius
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 180
                sweepAngle: 90
            }
        }
    }*/
    Shape {
        id: bottomRight

        x: bkg.x + bkg.width - bkg.radius * 2
        y: bkg.y + bkg.height - bkg.radius * 2
        antialiasing: true

        ShapePath {
            fillColor: "transparent"
            strokeColor: Constants.intermediateColor
            strokeWidth: 15

            PathAngleArc {
                centerX: bkg.radius
                centerY: bkg.radius
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 90
                sweepAngle: -90
            }
        }
    }

    Rectangle {
        x: bkg.x + bkg.radius
        y: bkg.y - height / 2
        width: 15
        height: 15
        radius: width
        color: Constants.intermediateColor
    }

    Rectangle {
        x: bkg.x - width / 2
        y: bkg.y + bkg.radius
        width: 15
        height: 15
        radius: width
        color: Constants.intermediateColor
    }

    Rectangle {
        x: bkg.x + bkg.width - width / 2
        y: bkg.y + bkg.height - bkg.radius - height
        width: 15
        height: 15
        radius: width
        color: Constants.intermediateColor
    }

    Rectangle {
        x: bkg.x + bkg.width - bkg.radius - width
        y: bkg.y + bkg.height - height / 2
        width: 15
        height: 15
        radius: width
        color: Constants.intermediateColor
    }

    Rectangle {
        id: loadIndicator
        x: bkg.x + bkg.radius
        y: bkg.y - height / 2
        width: 15
        height: 15
        radius: width
        color: Constants.intermediateColor
    }

    Text {
        id: subTitle
        anchors {
            horizontalCenter: parent.horizontalCenter
        }
        y: parent.height * 2 / 3

        text: qsTr("Démarrage en cours...")
        font {
            family: "Avenir Next"
            weight: Font.DemiBold
            pixelSize: root.height / 30
        }
        color: Constants.intermediateColor
    }
}
