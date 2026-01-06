import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property alias borderRadius: pnl.borderRadius
    property alias glassColor: pnl.glassColor
    property alias blurRadius: pnl.blurRadius
    property alias borderWidth: pnl.borderWidth
    property alias borderColor: pnl.borderColor
    property alias backgroundSource: pnl.backgroundSource
    property alias shadow: pnl.shadow
    property alias highlight: pnl.highlight
    property alias brightness: pnl.brightness
    property alias contrast: pnl.contrast
    property color shadowColor: "#111"

    // Le contenu à afficher sur le verre
    default property alias content: pnl.data

    PanelPrivate {
        id: pnl
        anchors.fill: parent
    }

    // Ombre portée autour du verre
    DropShadow {
        anchors.fill: pnl
        source: pnl
        radius: 25
        samples: 50
        color: root.shadowColor
        transparentBorder: true
    }
}
