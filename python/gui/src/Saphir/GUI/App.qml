// Copyright (C) 2021 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import QtQuick
import "components"
import "imports"

Window {
    visible: true
    //visibility: Window.Maximized
    minimumHeight: Constants.height
    minimumWidth: Constants.width
    title: "SAPHIR"

    SplashScreen {
        id: splashScreen
        anchors.fill: parent
    }

    Connections {
        target: Constants
        onHideSplashScreen: splashScreen.visible = false
    }

    Loader {
        id: mainWindowLoader
        visible: !splashScreen.visible
        source: Qt.resolvedUrl("MainScreen.qml")
        anchors.fill: parent

        function reloadWindow()
        {
            console.log("Reloading")
            mainWindowLoader.sourceComponent = null;
            mainWindowLoader.source = Qt.resolvedUrl("MainScreen.qml");
        }
    }

    Connections {
        target: Constants
        function onReloadRequested() {
            mainWindowLoader.reloadWindow()
        }

    }

}

