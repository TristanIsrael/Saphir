pragma Singleton
import QtQuick

QtObject {
    id: qtObject
    readonly property color colorOverlay: "#bb010101"
    readonly property color colorDark: "#eaeaea"
    readonly property color colorClear: "#010101"
    readonly property color colorBg: "#333333"
    readonly property color colorControl: "#aafafafa"
    readonly property color colorText: "#333333"
    readonly property color colorBorder: "#333333"
    readonly property color colorButtonEnabled: "#444480"
    readonly property color colorButtonDisabled: "#d8d8d8"
    readonly property color colorPanelEnabled: "#666666"
    readonly property color colorPanelDisabled: "#444480"
    readonly property color colorShadowEnabled: "#333333"
    readonly property color colorShadowDisabled: "#666666"
    readonly property color colorButtonTextEnabled: "#030303"
    readonly property color colorButtonTextDisabled: "#aafafafa"

    readonly property color colorFilterNotReady: "#00555555"
    readonly property color colorFilterReady: '#667f84f3'
    readonly property color colorFilterUsed: "#33ffa500"
    readonly property color colorFilterInfected: '#66ff2525'

    readonly property color colorClean: "#4caf50"
    readonly property color colorInfected: "#F44336"
    readonly property color colorWaiting: "#333333"
    readonly property color colorRunning: "#656dfd"
    readonly property color colorSelected: "#66656dfd"

    readonly property color colorIconFile: "#4DA8F1"
    readonly property color colorIconFolder: "#FFAEC0"

    readonly property color colorWarning: "#fc7304"
    readonly property color colorSuccess: "#4caf50"

    readonly property color colorNotProtected: "#4caf50"
    readonly property color colorRestricted: "#ffc107"
    readonly property color colorSecret: "#ff9800"
    readonly property color colorTopSecret: "#d32f2f"

    readonly property double panelSaturation: 0
    readonly property double panelBrightness: 0.05
    readonly property double logoBrightness: 0.0
}
