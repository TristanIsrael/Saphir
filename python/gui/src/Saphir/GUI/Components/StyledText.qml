import QtQuick
import Components

Text {
    id: root

    property int section: Constants.Section.Paragraph

    font.family: "Inter"
    text: ""
    color: Environment.colorText
    font.pixelSize: {
        switch(root.section) {
        case Constants.Section.Title1: return 24
        case Constants.Section.Title2: return 22
        case Constants.Section.Title3: return 20
        case Constants.Section.Paragraph: return 18
        case Constants.Section.Tiny: return 16
        case Constants.Section.SuperTiny: return 14
        }

        return 18
    }
}
