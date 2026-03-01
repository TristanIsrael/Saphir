import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Themes

Analysis {
    id: main    

    WfDialog {
        anchors.centerIn: parent
        label: "The analysis is finished.\nDo you want to copy the files?"

        buttonsLabels: [ "Yes", "No" ]
    }
}
