import QtQuick
import net.alefbet

ActionsPanelUi {
    id: root        

    Connections {
        target: ApplicationController
        
        function onAnalysisReadyChanged() {
            updateStartStopState()
        }

        function onQueueSizeChanged() {
            updateStartStopState()
        }
    }

    Connections {
        target: btnStartPauseResumeAnalysis

        function onClicked() {
            ApplicationController.start_stop_analysis()
        }
    }

    /*Component.onCompleted: function() {
        updateState()
    }*/

    function updateState() {          
        console.debug("****System State****", ApplicationController.systemState)  

        /*switch(ApplicationController.systemState) {
            case Enums.SystemState.SystemInactive: state = ""; break;
            case Enums.SystemState.SystemStarting: state = "starting"; break;
            case Enums.SystemState.SystemWaitingForDevices: state = "waiting"; break;
            case Enums.SystemState.SystemReady: state = "ready"; break;
            case Enums.SystemState.SystemRunning: state = "running"; break;
        }*/
    }

    function updateStartStopState() {
        root.btnStartPauseResumeAnalysis.enabled = ApplicationController.queueSize > 0 && ApplicationController.analysisReady
    }
}
