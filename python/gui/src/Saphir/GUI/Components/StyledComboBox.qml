import QtQuick
import QtQuick.Controls

ComboBox {
    id: root

    //model: [ "EFI", "DISK NAME", "Ma partition" ]

    delegate: ItemDelegate {
        id: delegate

        required property var model
        required property int index

        width: root.width
        contentItem: StyledText {
            text: delegate.model[root.textRole]
        }
        highlighted: root.highlightedIndex === index
    }

    contentItem: StyledText {
        leftPadding: 0
        rightPadding: root.indicator.width + root.spacing

        text: root.displayText
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Item {
        implicitWidth: 140
        implicitHeight: 40

        /*border {
          color: "transparent"
            width: 2
            color: Environment.colorBorder
        }*/
    }

    indicator: Icon {
        x: root.width - width - root.rightPadding/2
        y: root.topPadding + (root.availableHeight - height) / 2
        text: "\ue5c6"
        visible: root.model.length > 1
    }

    popup: Popup {
        y: root.height - 1
        width: root.width
        height: Math.min(contentItem.implicitHeight, root.Window.height - topMargin - bottomMargin)
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: Qt.rgba(Environment.colorControl.r, Environment.colorControl.g, Environment.colorControl.b, 0.8)
            radius: 2
        }
    }

}
