# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add libs for weasyprint
LIBS = [
    "libpango-1.0.so.0",
    "libpangocairo-1.0.so.0",
    "libpangoft2-1.0.so.0",
    "libpangoxft-1.0.so.0",
    "libharfbuzz.so.0",
    "libharfbuzz-subset.so.0",
    "libharfbuzz-raster.so.0",
    "libharfbuzz-vector.so.0",
    "libgobject-2.0.so.0",
    "libglib-2.0.so.0",
    "libfribidi.so.0",    
    "libfontconfig.so.1",
]

binaries = []
for lib in LIBS:
    for d in ("/usr/lib", "/lib"):
        path = os.path.join(d, lib)
        if os.path.exists(path):
            binaries.append((path, "."))
            break
    else:
        print(f"WARNING : {lib} not found")

hiddenimports = (
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "PySide6.QtNetwork",
    "jinja2",
    "weasyprint",
    "cairocffi",
    "cffi",
    "gi",
    ["_cffi_backend"]
    + collect_submodules("tinyhtml5")
    + collect_submodules("fontTools")
)

datas = (
    [("src/Saphir/GUI", "GUI"),
    ("src/Saphir/i18n", "i18n"),
    ("src/Saphir/fonts", "fonts"),
    ("src/Saphir/Saphir", "Saphir")] 
    + collect_data_files("weasyprint") 
    + collect_data_files("pyphen")    
)
#+ [("/usr/share/fonts/dejavu", "fonts")]   # embedded fonts

a = Analysis(
    ['src/Saphir/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime-hooks/system-site-packages.py'],
    excludes=['safecor', 'libsaphir'],
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
