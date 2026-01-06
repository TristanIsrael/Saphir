// Copyright (C) 2025 The Qt Company Ltd.
// SPDX-License-Identifier: BSD-3-Clause

import QtQuick

ShaderEffect {
    id: rootItem
    property Item src: null
    property vector2d offset: Qt.vector2d((1.0 + parent.blurMultiplier) / width,
                                          (1.0 + parent.blurMultiplier) / height)
    visible: false
    layer.enabled: true
    layer.smooth: true
    vertexShader: "bluritems.vert.qsb"
    fragmentShader: "bluritems.frag.qsb"
}
