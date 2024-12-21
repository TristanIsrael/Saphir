import QtQuick
import net.alefbet

EcranPrincipalUi {
    id: root

    Connections {
        target: ApplicationController
        
        function onShowMessage(title, message, alert, modal) {
            root.msgBox.title = title
            root.msgBox.message = message
            root.msgBox.alert = alert
            root.msgBox.modal = modal
            root.msgBox.visible = true
        }
    }

}