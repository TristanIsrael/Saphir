import QtQuick

StatePanelUi {
    id: root

    onStateChanged: function() {
        console.debug("Current state:", state)
    }
}
