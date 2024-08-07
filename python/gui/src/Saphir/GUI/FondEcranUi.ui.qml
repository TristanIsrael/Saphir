import QtQuick
import QtQuick.Controls

Rectangle {
    id: rectangle
    width: Constants.width
    height: Constants.height

    color: Constants.backgroundColor

    property int headerHeight: entete.height

    EnTete {
        id: entete

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }
    }
}
