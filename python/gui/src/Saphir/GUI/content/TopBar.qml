import QtQuick
import Components

TopBarUi {
    id: root

    property bool timeFormatZulu: true

    /* Composition */ 
    lblRestriction.text: {
        switch (bindings.classificationLevel) {
        case 0:
            return qsTr("Not protected")
        case 1:
            return qsTr("Restricted")
        case 2:
            return qsTr("Secret")
        case 3:
            return qsTr("Top Secret")
        }

        return qsTr("Not protected")
    }
    lblRestriction.color: {
        switch (bindings.classificationLevel) {
        case 0:
            return Environment.colorNotProtected
        case 1:
            return Environment.colorRestricted
        case 2:
            return Environment.colorSecret
        case 3:
            return Environment.colorTopSecret
        }

        return qsTr("Not protected")
    }

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
