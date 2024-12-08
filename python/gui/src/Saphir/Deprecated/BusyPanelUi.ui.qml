import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Item {
    id: root
    
    visible: true //ApplicationController.taskRunning

    Rectangle {
        id: bkg
        anchors.centerIn: parent 
        height: parent.height/5
        width: height
        color: Constants.popupBackgroundColor
        opacity: 0.8

        BusyIndicator {
            height: parent.height*0.7
            width: height
            anchors.centerIn: parent
            running: true
        }
    }
}
