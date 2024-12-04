pragma Singleton
import QtQuick

QtObject {
    readonly property int width: 1280
    readonly property int height: 800

    property string relativeFontDirectory: "fonts"

    /* Edit this comment to add your custom font */
    readonly property font font: Qt.font({
                                             family: Qt.application.font.family,
                                             pixelSize: Qt.application.font.pixelSize
                                         })
    readonly property font largeFont: Qt.font({
                                                  family: Qt.application.font.family,
                                                  pixelSize: Qt.application.font.pixelSize * 1.6
                                              })    

    readonly property color backgroundColor: "#f2f2f2"
    readonly property color progressColor: "#c2c2c2"
    readonly property color selectionColor: "#a2adda"
    readonly property color contrastColor: "#ffffff"
    readonly property color intermediateColor: "#384454" //"#2d396b"
    readonly property color titleColor: intermediateColor
    readonly property color alertColor: "#dd121c"
    readonly property color errorColor: "#dd121c"
    readonly property color headingColor: "#53585F"
    readonly property color paragraphColor: "#111"
    readonly property color buttonColor: intermediateColor
    readonly property color successColor: "#499636"
    readonly property color disabledColor: "#d5d5d5"
    readonly property color textColor: "#111"
    readonly property color popupBackgroundColor: "#444"
}
