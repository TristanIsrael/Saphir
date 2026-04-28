# -*- mode: python ; coding: utf-8 -*-
import os
base_dir = os.path.abspath(os.getcwd())

datas = [
    ("src/Saphir/GUI", "GUI"),
    ("src/Saphir/i18n", "i18n"),
    ("src/Saphir/fonts", "fonts"),
    ("src/Saphir/Saphir", "Saphir")
]

a = Analysis(
    ['src/Saphir/main.py'],
    pathex=[
        os.path.join(base_dir, "../../../Safecor/python/lib/src")
    ],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtNetwork",
        "PySide6.QtWidgets",
        "jinja2"
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Remove unnecessary libraries
a.binaries = [
    b for b in a.binaries if not any(x in b[0] for x in [
        "Qt3D",
        "QtBluetooth",                
        "QtDataVisualization",
        "QtCharts",
        "QtLocation",
        "QtMultimedia",
        "QtPositioning",
        "QtQuick3D",
        "QtScxml",
        "QtQuickTimeline",
        "QtRemoteObjects",
        "QtSensors",
        "QtSpatialAudio",
        "QtSql",
        "QtStateMachine",
        "QtSvg",
        "QtTest",
        "QtTextToSpeech",
        "QtWeb",
        "Qt63D",
        "Qt6Bluetooth",                
        "Qt6DataVisualization",
        "Qt6Charts",
        "Qt6Location",
        "Qt6Multimedia",
        "Qt6Positioning",
        "Qt6Quick3D",
        "Qt6Quick3DUtils",
        "Qt6Scxml",
        "Qt6QmlNetwork",
        "Qt6QuickDialogs",
        "Qt6QuickTimeline",
        "Qt6QuickTimelineBlendTrees",
        "Qt6RemoteObjects",
        "Qt6Sensors",
        "Qt6SpatialAudio",
        "Qt6Sql",
        "Qt6StateMachine",
        "Qt6StateMachineQml",
        "Qt6Svg",
        "Qt6Test",
        "Qt6TextToSpeech",
        "Qt6Web"
    ])
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='saphir-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
#coll = COLLECT(
#    exe,
#    a.binaries,
#    a.datas,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    name='saphir-viewer',
#)
