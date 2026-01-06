import QtQuick
import net.alefbet

StatePanelUi {
    id: root

    Connections {
        target: ApplicationController
        
        function onSystemStateChanged(systemState) {
            console.debug("Current system state:", systemState)
            //SystemInactive, SystemStarting, SystemWaitingForDevice, SystemReady, SystemWaitingForUserAction, SystemGettingFilesList, SystemAnalysisRunning = range(7)
            switch(systemState) {            
                case Enums.SystemState.SystemInactive: root.state = "waiting"; break;
                case Enums.SystemState.SystemStarting: root.state = "starting"; break;
                case Enums.SystemState.SystemWaitingForDevice: root.state = "inactive"; break;
                case Enums.SystemState.SystemReady: root.state = "ready"; break;
                case Enums.SystemState.SystemWaitingForUserAction: root.state = "waiting_for_user"; break;
                case Enums.SystemState.SystemGettingFilesList: root.state = "getting_files_list"; break;
                case Enums.SystemState.SystemAnalysisRunning: root.state = "analysis_running"; break;
            }
        }
    }
}
