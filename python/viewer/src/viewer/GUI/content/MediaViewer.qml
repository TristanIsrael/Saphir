import QtQuick
import QtMultimedia

Item {
    id: root
    
    property string filePath: bindings.currentFilepath

    VideoOutput {
        id: videoOut

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            bottom: mediaControl.top
        }
    }

    MediaPlayer {
        id: mediaPlayer

        videoOutput: videoOut
        audioOutput: AudioOutput {
            id: audio 
            //volume: 
        }

        autoPlay: true
        source: root.visible ? "file:///" + bindings.repositoryPath + root.filePath : ""        
    }

    MediaControl {
        id: mediaControl

        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        durationInMillis: mediaPlayer.duration
        positionInMillis: mediaPlayer.position
        playing: mediaPlayer.playbackState === MediaPlayer.PlayingState

        Connections {
            function onPause() {
                mediaPlayer.pause()
            }

            function onPlay() {
                mediaPlayer.play()
            }

            function onStop() {
                mediaPlayer.stop()
            }
        }
    }

    Bindings {
        id: bindings
    }
}