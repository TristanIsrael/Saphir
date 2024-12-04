import QtQuick
import net.alefbet

ActionsPanelUi {
    id: root        

    /*Connections {
        target: ApplicationController
        
        function onAnalysisReadyChanged() {
            updateStartStopState()
        }

        function onQueueSizeChanged() {
            updateStartStopState()
        }
    }*/

    Connections {
        target: btnStartPauseResumeAnalysis

        function onClicked() {
            ApplicationController.start_stop_analysis()
        }
    }

    Connections {
        target: btnStartTransfer

        function onClicked() {
            ApplicationController.start_transfer()
        }
    }


}
