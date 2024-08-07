import QtQuick

ListModel {    

    ListElement {
        type: "file"
        filename: "Une petite image.png"
        filepath: "/"
        filesize: 320112
        progress: 100
        selected: false
    }

    ListElement {
        type: "file"
        filename: "C'est un beau roman.pdf"
        filepath: "/"
        filesize: 24378273
        progress: 100
        selected: false
    }

}
