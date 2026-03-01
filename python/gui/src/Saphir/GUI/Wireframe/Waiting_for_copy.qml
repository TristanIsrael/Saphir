import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Components
import Themes

Analysis {
    id: main

    WfDialog {
        anchors.centerIn: parent
        label: "Please connect a storage for copy.\nDon't remove the source storage."

        buttonsLabels: [ "Cancel" ]
    }
}
