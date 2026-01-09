import QtQuick
import Qt5Compat.GraphicalEffects
import Components
import Themes

WfMain {
    id: main        

    WfDialog {
        id: wfPanel

        anchors.centerIn: parent
        label: "Please connect a disk"

        buttonsLabels: [ ]
    }
}
