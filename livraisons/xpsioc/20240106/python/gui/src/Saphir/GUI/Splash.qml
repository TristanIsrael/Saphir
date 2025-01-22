import QtQuick

SplashUi {
    id: root

    SequentialAnimation on shadow.color {
        loops: Animation.Infinite
        running: true

        ColorAnimation {
            from: Constants.contrastColor
            to: Constants.intermediateColor
            easing.type: Easing.OutInSine
            duration: 2000
        }

        ColorAnimation {
            from: Constants.intermediateColor
            to: Constants.contrastColor
            easing.type: Easing.OutInSine
            duration: 2000
        }
    }

    /*SequentialAnimation  on subTitle.opacity {
        loops: Animation.Infinite
        running: false

        PropertyAnimation {
            from: 1.0
            to: 0.0
            duration: 1000
            easing.type: Easing.InOutQuad
        }
        PropertyAnimation {
            from: 0.0
            to: 1.0
            duration: 1000
            easing.type: Easing.InOutQuad
        }
    }

    PathAnimation {
        target: loadIndicator
        easing.type: Easing.InOutQuad
        loops: Animation.Infinite

        path: Path {
            startX: loadIndicator.x
            startY: loadIndicator.y

            PathCurve {
                x: bkg.x+bkg.width-bkg.radius
                y: bkg.y-loadIndicator.height/2
            }

            PathAngleArc {
                centerX: bkg.x+bkg.width-bkg.radius-loadIndicator.width/2
                centerY: bkg.y+bkg.radius-loadIndicator.height/2
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: -90
                sweepAngle: 90
            }

            PathCurve {
                x: bkg.x+bkg.width-loadIndicator.width/2
                y: bkg.y+bkg.height-bkg.radius
            }

            PathAngleArc {
                moveToStart: false
                centerX: bkg.x+bkg.width-bkg.radius-loadIndicator.width/2
                centerY: bkg.y+bkg.height-bkg.radius-loadIndicator.height/2
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 0
                sweepAngle: 90
            }

            PathCurve {
                x: bkg.x+bkg.radius
                y: bkg.y+bkg.height-loadIndicator.height/2
            }

            PathAngleArc {
                moveToStart: true
                centerX: bkg.x+bkg.radius-loadIndicator.width/2
                centerY: bkg.y+bkg.height-bkg.radius-loadIndicator.height/2
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 90
                sweepAngle: 90
            }

            PathCurve {
                x: bkg.x-loadIndicator.width/2
                y: bkg.y+bkg.radius
            }

            PathAngleArc {
                centerX: bkg.x+bkg.radius-loadIndicator.width/2
                centerY: bkg.y+bkg.radius-loadIndicator.height/2
                radiusX: bkg.radius
                radiusY: bkg.radius
                startAngle: 180
                sweepAngle: 90
            }
        }

        duration: 2000
        running: false
    }*/

}
