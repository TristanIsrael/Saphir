import QtQuick

Text {
    enum TextLevel {
        H1,
        H2,
        H3,
        H4,
        Paragraph,
        Indice
    }

    property int level: PText.TextLevel.Paragraph

    font {
        //family: "Avenir Next"
        family: "Roboto"
        weight: Font.DemiBold
        pointSize: level === PText.TextLevel.H1 ? 38 : level === PText.TextLevel.H2 ? 32 : level === PText.TextLevel.H3 ? 28 : level === PText.TextLevel.H4 ? 24 : level === PText.TextLevel.Paragraph ? 20 : 18
    }

    color: level === PText.TextLevel.Paragraph ? Constants.paragraphColor : Constants.headingColor
    clip: true
}
