// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: BSD-3-Clause

import QtQuick

Item {
    id: rootItem
    property alias blurSrc1: blurredItemSource1
    property alias blurSrc2: blurredItemSource2
    property alias blurSrc3: blurredItemSource3
    property alias blurSrc4: blurredItemSource4
    property alias blurSrc5: blurredItemSource5
    property Item source: null

    QtObject {
        id: priv
        property bool useBlurItem2: rootItem.blurMax > 2
        property bool useBlurItem3: rootItem.blurMax > 8
        property bool useBlurItem4: rootItem.blurMax > 16
        property bool useBlurItem5: rootItem.blurMax > 32
    }

    BlurItem {
        id: blurredItemSource1
        src: rootItem.source
        // Size of the first blurred item is by default half of the source.
        // Increase for quality and decrease for performance & more blur.
        readonly property int blurItemSize: 8
        width: Math.ceil((rootItem.source ? rootItem.source.width : 16) / 16) * blurItemSize
        height: Math.ceil((rootItem.source ? rootItem.source.height : 16) / 16) * blurItemSize
    }
    BlurItem {
        id: blurredItemSource2
        src: priv.useBlurItem2 ? blurredItemSource1 : null
        width: blurredItemSource1.width * 0.5
        height: blurredItemSource1.height * 0.5
    }
    BlurItem {
        id: blurredItemSource3
        src: priv.useBlurItem3 ? blurredItemSource2 : null
        width: blurredItemSource2.width * 0.5
        height: blurredItemSource2.height * 0.5
    }
    BlurItem {
        id: blurredItemSource4
        src: priv.useBlurItem4 ?  blurredItemSource3 : null
        width: blurredItemSource3.width * 0.5
        height: blurredItemSource3.height * 0.5
    }
    BlurItem {
        id: blurredItemSource5
        src: priv.useBlurItem5 ? blurredItemSource4 : null
        width: blurredItemSource4.width * 0.5
        height: blurredItemSource4.height * 0.5
    }
}
