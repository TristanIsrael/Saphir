import QtQuick

Rectangle {
    id: root

    property string text
    property bool checked: false

    signal clicked()

    implicitWidth: icnCheck.width + icnCheck.x
    implicitHeight: 40
    color: checked ? Environment.colorButtonEnabled : Environment.colorControl
    radius: 5

    StyledText {
        id: lbl
        x: 10
        y: (parent.height - height) / 2
        text: root.text
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        color: root.checked ? Environment.colorDark : Environment.colorClear
    }

    Icon {
        id: icnCheck
        visible: root.checked
        x: lbl.width + lbl.x + 10
        y: (parent.height - height) / 2
        text: Constants.iconTick
        width: visible ? implicitWidth : 0
        color: Environment.colorDark
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            root.clicked()
        }
    }
}
