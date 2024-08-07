import QtQuick

Text {
    id: root

    property int pixelSize: 32
    property bool pressed: mArea.containsPress

    signal clicked()    

    text: ""
    font.pixelSize: root.pixelSize
    font.family: "Material Icons"
    color: enabled ? Constants.buttonColor : Constants.disabledColor

    MouseArea {
        id: mArea
        anchors.fill: parent
        onClicked: root.clicked()
    }
}
