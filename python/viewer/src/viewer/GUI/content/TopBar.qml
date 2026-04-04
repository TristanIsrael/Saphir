import QtQuick
import Components

TopBarUi {
    id: root

    property bool timeFormatZulu: true

    Timer {
        triggeredOnStart: true
        interval: 1000
        running: true
        repeat: true
        onTriggered: updateTime()
    }

    /* Slots */
    Connections {
        target: maHour
        function onClicked() {
            timeFormatZulu = !timeFormatZulu
            updateTime()
        }
    }

    Component.onCompleted: function() {
        updateTime()
    }

    // Functions
    function updateTime() {
        //Conversion en TZ Zulu
        const now = new Date()
        const zulu = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDay(), now.getUTCHours(), now.getUTCMinutes(), now.getUTCSeconds())
        const localTime = Qt.formatTime(new Date(), "HH:mm:ss");
        const zuluTime = Qt.formatTime(zulu, "HH:mm:ssZ");
        lblTime.text = timeFormatZulu ? zuluTime : localTime
    }

    Bindings {
        id: bindings
    }

}
