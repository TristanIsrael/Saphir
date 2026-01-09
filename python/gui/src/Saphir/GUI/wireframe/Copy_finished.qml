import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Themes

Copy_files {
    id: main    

    WfDialog {
        anchors.centerIn: parent
        label: "The copy is finished."

        buttonsLabels: [ "Shutdown", "Restart" ]
    }
}
