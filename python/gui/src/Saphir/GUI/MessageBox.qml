import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

Item {
    id: root

    property alias title: lblTitle.text
    property alias message: lblMessage.text
    property alias btnClose: btnClose
    property bool modal: false
    property bool alert: false

    implicitHeight: Screen.height
    implicitWidth: Screen.width

    /*width: implicitWidth
    implicitWidth: lyt.width + 16
    height: implicitHeight
    implicitHeight: lyt.height + 16*/

    Rectangle {
        id: bkg
        anchors.fill: parent
        color: Constants.popupBackgroundColor
        opacity: 0.9
        visible: root.modal        
    }    

    Rectangle {
        width: parent.width/3
        height: parent.height/3
        anchors.centerIn: parent
        color: root.modal ? "transparent": bkg.color
        radius: height / 10

        ColumnLayout {
            id: lyt

            y: 8
            anchors {
                fill: parent
                centerIn: parent
                margins: 8            
            }

            PText {
                id: lblTitle
                Layout.preferredWidth: parent.width

                color: root.alert ? Constants.errorColor : Constants.progressColor
                horizontalAlignment: Text.AlignHCenter
                level: PText.TextLevel.H4
                font.bold: true
                visible: text !== ""
            }

            PText {
                id: lblMessage
                Layout.preferredWidth: parent.width

                text: qsTr("An explanation to help the user understand what is supposed to happen here.")
                color: Constants.contrastColor
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                level: PText.TextLevel.H4
            }

            Rectangle {
                id: btnClose
                color: "transparent"
                radius: 5
                width: btnTxt.width*1.4
                height: btnTxt.height*1.4
                Layout.alignment: Qt.AlignHCenter

                border {
                    color: Constants.contrastColor
                    width: 2
                }

                PText {
                    id: btnTxt
                    anchors.centerIn: parent
                    text: qsTr("Close")
                    color: Constants.contrastColor                    
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: function() {
                        root.visible = false
                    }
                }
            }
        }
    }
}
