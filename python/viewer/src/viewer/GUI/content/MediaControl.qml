import QtQuick
import Components

Item {
    id: root

    property int positionInMillis
    property int durationInMillis
    property bool playing: false

    implicitWidth: 800
    implicitHeight: 50

    signal pause()
    signal play()
    signal stop()

    Icon {
        id: btnPlayStop

        anchors {
            verticalCenter: parent.verticalCenter
            left: parent.left
            leftMargin: 10
        }

        height: parent.height
        width: parent.height

        color: Environment.colorText
        text: root.playing ? Constants.iconPause : Constants.iconStart

        Connections {
            function onClicked() {
                if(root.playing) {
                    root.pause()
                } else {
                    root.play()
                }
            }
        }
    }

    StyledText {
        id: lblCurrentTimestamp

        anchors {
            verticalCenter: parent.verticalCenter
            left: btnPlayStop.right
            leftMargin: 10
        }

        text: "00:00:00"
        color: Environment.colorText
    }

    Rectangle {
        id: progressContainer

        anchors {
            left: lblCurrentTimestamp.right
            leftMargin: 10
            right: lblDuration.left
            rightMargin: 10
            verticalCenter: parent.verticalCenter
        }

        height: 10
        radius: 10
        color: "#99ffffff"

        Rectangle {
            id: rctProgress
            anchors {
                left: parent.left
                top: parent.top
                bottom: parent.bottom
            }

            width: parent.width * (root.positionInMillis / root.durationInMillis)
            radius: parent.radius
            color: Environment.colorControl
        }
    }

    StyledText {
        id: lblDuration

        anchors {
            right: parent.right
            rightMargin: 10
            verticalCenter: parent.verticalCenter
        }

        text: "00:00:00"
        color: Environment.colorText
    }

    onDurationInMillisChanged: function() {
        const strDuration = timeToString(root.durationInMillis)
        lblDuration.text = strDuration
    }

    onPositionInMillisChanged: function() {
        const strPosition = timeToString(root.positionInMillis)
        lblCurrentTimestamp.text = strPosition
    }

    onVisibleChanged: function() {
        if(!visible) {
            root.stop()
        }
    }

    /** Functions */
    function timeToString(timeInMillis) {
        const totalSeconds = Math.floor(timeInMillis / 1000)
        const hours = Math.floor(totalSeconds / 3600)
        const minutes = Math.floor(totalSeconds / 60)
        const seconds = totalSeconds % 60

        function pad(n) {
            return n < 10 ? "0" + n : n
        }

        return pad(hours) +":" +pad(minutes) +":" +pad(seconds)
    }
}
