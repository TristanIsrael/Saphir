import QtQuick
import Components

Rectangle {
    property bool discreet: false

    width: 640
    height: 480

    color: discreet ? "transparent" : Environment.colorControl

    border {
        width: discreet ? 0 : 2
        color: Environment.colorBorder
    }
}
