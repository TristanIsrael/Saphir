pragma Singleton
import QtQuick

QtObject {
    id: qtObject
    readonly property color colorOverlay: "#bb010101"
    readonly property color colorDark: "#333333"
    readonly property color colorClear: "#555555"
    readonly property color colorBg: "#111111"
    readonly property color colorControl: "#111111"
    readonly property color colorText: "#333333"
    readonly property color colorBorder: "#222222"
    readonly property color colorButtonEnabled: "#555555"
    readonly property color colorButtonDisabled: "#333333"
    readonly property color colorPanelEnabled: '#1f1f3a'
    readonly property color colorPanelDisabled: "#666666"
    readonly property color colorShadowEnabled: '#44a08e8e'
    readonly property color colorShadowDisabled: '#002c2c2c'
    readonly property color colorButtonTextEnabled: "#333333"
    readonly property color colorButtonTextDisabled: "#222222"

    readonly property color colorFilterNotReady: '#292c30'
    readonly property color colorFilterReady: '#1a1c41'
    readonly property color colorFilterUsed: '#6a4501'
    readonly property color colorFilterInfected: '#5f0000'

    readonly property color colorClean: '#163617'
    readonly property color colorInfected: '#410101'
    readonly property color colorWaiting: '#99535252'

    readonly property color colorSelected: '#66191b43'

    readonly property color colorIconFile: '#193953'
    readonly property color colorIconFolder: '#461822'

    readonly property color colorWarning: '#893f02'

    readonly property color colorNotProtected: '#1c441d'
    readonly property color colorRestricted: '#493701'
    readonly property color colorSecret: '#633c01'
    readonly property color colorTopSecret: '#681616'

    readonly property double panelSaturation: 0.1
    readonly property double panelBrightness: 0.05
    readonly property double logoBrightness: -0.09
}
