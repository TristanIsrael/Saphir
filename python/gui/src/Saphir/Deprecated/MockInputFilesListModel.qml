import QtQuick

ListModel {

    ListElement {
        type: "up"
    }

    ListElement {
        type: "file"
        filename: "Le rapport du rapport.pdf"
        filepath: "/"
        filesize: 1400123
        selected: false
        progress: 100
        infected: true
    }

    ListElement {
        type: "file"
        filename: "Une petite image.png"
        filepath: "/"
        filesize: 320112
        selected: false
        progress: 100
        infected: false
    }

    ListElement {
        type: "file"
        filename: "C'est un beau roman.pdf"
        filepath: "/"
        filesize: 24378273
        progress: 100
        infected: false
    }

    ListElement {
        type: "folder"
        filename: "binaires"
        filepath: "/"
    }

    ListElement {
        type: "file"
        filename: "setup.exe"
        filepath: "/binaires/"
        filesize: 131921921
        selected: false
        progress: 34
    }

    ListElement {
        type: "file"
        filename: "setup-2.bin"
        filepath: "/binaires/"
        filesize: 635762336
        selected: false
        progress: 79
    }

    ListElement {
        type: "file"
        filename: "setup-4.bin"
        filepath: "/binaires/autres/"
        filesize: 37716611
        selected: false
    }

    ListElement {
        type: "folder"
        filename: "autres"
        filepath: "/"
    }

    ListElement {
        type: "file"
        filename: "setup-3.bin"
        filepath: "/autres/"
        filesize: 23373236
        selected: true
        progress: 0        
    }
}
