import QtQuick

EnTeteUi {
    id: root

    Timer {
        interval: 1000
        repeat: true
        running: true
        triggeredOnStart: true

        onTriggered: {
            lblCurrentTime.text = new Date().toLocaleTimeString(Qt.locale("fr_FR"), "HH:mm")
        }
    }
}