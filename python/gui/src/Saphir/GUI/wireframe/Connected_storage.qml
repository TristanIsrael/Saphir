import QtQuick
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main   

    WfDialog {
        id: wfPanel

        anchors.centerIn: parent
        label: "Do you want to analyze the whole storage?"
        buttonsLabels: [ "Yes", "Select files" ]
    }
}
