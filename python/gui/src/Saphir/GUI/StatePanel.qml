import QtQuick
import net.alefbet

StatePanelUi {
    id: root

    Connections {
        target: ApplicationController
        
        onSystemStateChanged: function() {
            console.debug("Current system state:", ApplicationController.systemState)
            console.debug("blah:", Enums.SystemState.SystemRunning)
            switch(ApplicationController.systemState) {            
                case Enums.SystemState.SystemWaitingForDevice: "waiting"
                case Enums.SystemState.SystemStarting: root.state = "starting"           
                case Enums.SystemState.SystemInactive: root.state = "inactive"
                case Enums.SystemState.SystemReady: root.state = "ready"
                case Enums.SystemState.SystemRunning: root.state = "running"
            }
        }
    }
}
