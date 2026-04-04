import QtQuick
import Components

Text {
    id: root

    font.family: "Material Symbols Outlined"
    text: {
        if(bindings.ambientLight > 66) {
            return "\ue81a"
        } else if(bindings.ambientLight > 33) {
            return "\uf02a"
        }

        return "\uf036"
    }
    font.pixelSize: 28
    font.bold: true
    color: Environment.colorText

    Bindings {
        id: bindings
    }
}
