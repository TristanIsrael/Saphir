pragma Singleton
import QtQuick
import Components
import Themes

QtObject {

    property bool handheld: false
    property bool portrait: false

    property string theme: Constants.light

    property int mainWidth: 1200
    property int mainHeight: 800

    property color colorControl: ThemeWireframe.control
    property color colorText: ThemeWireframe.text
    property color colorBorder: ThemeWireframe.border
    property color colorBg: ThemeWireframe.bg
}
