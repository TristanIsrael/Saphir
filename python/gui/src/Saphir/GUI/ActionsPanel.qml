import QtQuick
import net.alefbet

ActionsPanelUi {
    id: root    

    Connections {
        target: ApplicationController

        function onStatusChanged() {
            updateState()
        }

        function onSystemStateChanged() {
            updateState()
        }

        function onQueueSizeChanged() {
            root.btnStartPauseResumeAnalysis.enabled = ApplicationController.queueSize > 0
        }
    }

    Component.onCompleted: function() {
        updateState()
    }

    function updateState() {    
        console.debug("****STATUS****", ApplicationController.status)            
        console.debug("****STATE****", ApplicationController.systemState)  

        switch(ApplicationController.status) {
            case Enums.Status.Inactive: state = ""; break;
            case Enums.Status.Starting: state = "starting"; break;
            case Enums.Status.WaitingForDevices: state = "waiting"; break;
            case Enums.Status.Ready: state = "ready"; break;
            case Enums.Status.Running: state = "running"; break;
        }
    }
}
