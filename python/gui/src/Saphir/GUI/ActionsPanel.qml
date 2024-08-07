import QtQuick
import net.alefbet

ActionsPanelUi {
    id: root    

    Connections {
        target: ApplicationController
        function onStatusChanged() {
            statusChanged()
        }
    }

    Component.onCompleted: function() {
        statusChanged()
    }

    function statusChanged() {        
        console.debug(Enums.Status.WaitingForDevices)
        switch(ApplicationController.status) {
            case Enums.Status.Inactive: state = ""; break;
            case Enums.Status.Starting: state = "starting"; break;
            case Enums.Status.WaitingForDevices: console.debug("SBOUB"); state = "waiting"; break;
            case Enums.Status.Ready: state = "ready"; break;
            case Enums.Status.Running: state = "running"; break;
        }
    }
}
