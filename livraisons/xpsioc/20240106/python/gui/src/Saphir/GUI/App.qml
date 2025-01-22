// Copyright (C) 2021 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only

import QtQuick
import net.alefbet

Window {    
    id: window

    property bool themeClair: true
    property bool pret: ApplicationController.pret

    visible: true
    title: "Panoptiscan"

    width: Constants.width
    height: Constants.height

    Splash {
        id: splash
        visible: !pret
        anchors.fill: parent
    }

    EcranPrincipal {
        id: mainScreen
        anchors.fill: parent
        visible: pret
    }

}

