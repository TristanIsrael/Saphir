import QtQuick
import net.alefbet

EcranPrincipalUi {
    id: root

    Connections {
        target: ApplicationController
        
        function onShowMessage(title, message, alert) {
            root.msgBox.title = title
            root.msgBox.message = message
            root.alert = alert
        }
    }

}