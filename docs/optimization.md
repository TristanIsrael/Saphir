This page explains different optimization tactics

## Reduce memory footprint in `sys-gui`

Memory footprint:

After py3-pyside6 install:
```
- RAM used: 99 MB
- Disk used: 1.1 GB
  - /usr/: 1.1 GB
    - lib/: 959 MB
      - libLLVM.so.19.1: 153.6 MB
      - gallium-pipe/: 83 MB
      - libgallium-24.2.8.so: 37 MB
      - python3.12/: 33.6 MB
    - share/: 109.5 MB
      - qt6/: 47.4 MB
        **- translations/: 34.9 MB -> QtWebEngine locales**
        **- resources/: 12.5 MB -> QtWebEngine resources**
      - icu/: 29.4 MB
    - lib/: 959 MB
      **- libQt6WebEngineCore.so.6.8.2: 168MB -> QtWebEngine**
      - libLLVM.so.19.1: 153.6 MB
      - python3.12/: 85 MB
      *- gallium-pipe/: 83 MB -> MESA*
      - qt6/: 67.6 MB
        - libexec/: 24 MB
          - webenginedriver: 15.4 MB
          - gn: 3.3 MB
        - qml/: 19.3 MB
          - QtQuick/: 12.2 MB
            *- Controls/: 9.5 MB*
            **- QtQuick3D/: 3.4 MB**
            **- Qt3D**
            **- QtWayland**
        - metatypes/: 11.2 MB
        - plugins/: 9.6 MB
          - renderers/: 1.6 MB
          **- qmlls/: 1.3 MB**
        - bin/: 2.9 MB
          **- materialeditor: 2.3 MB**
      - llvm19/: 63.8 MB
      **- libgallium-24.2.8.so: 37 MB -> MESA**
      **- libx265...so: 18.8 MB -> Multimedia**
      **- libavcodec...so: 15.7 MB -> Multimedia**
      **- libSvtAv1Enc...so: 6.5 MB -> Multimedia**
      **- libQt6Designer...so: 5.4 MB -> Multimedia**
      **- other multimedia libs**

```

List of library used by python3 with Saphir GUI:

```
/lib/ld-musl-x86_64.so.1
/usr/lib/libEGL.so.1.0.0
/usr/lib/libGL.so.1.2.0
/usr/lib/libLLVM.so.19.1
/usr/lib/libQt6Core.so.6.8.2
/usr/lib/libQt6DBus.so.6.8.2
/usr/lib/libQt6Gui.so.6.8.2
/usr/lib/libQt6Network.so.6.8.2
/usr/lib/libQt6OpenGL.so.6.8.2
/usr/lib/libQt6Pdf.so.6.8.2
/usr/lib/libQt6Qml.so.6.8.2
/usr/lib/libQt6QmlMeta.so.6.8.2
/usr/lib/libQt6QmlModels.so.6.8.2
/usr/lib/libQt6QmlWorkerScript.so.6.8.2
/usr/lib/libQt6Quick.so.6.8.2
/usr/lib/libQt6QuickControls2.so.6.8.2
/usr/lib/libQt6QuickControls2Basic.so.6.8.2
/usr/lib/libQt6QuickControls2Impl.so.6.8.2
/usr/lib/libQt6QuickEffects.so.6.8.2
/usr/lib/libQt6QuickLayouts.so.6.8.2
/usr/lib/libQt6QuickShapes.so.6.8.2
/usr/lib/libQt6QuickTemplates2.so.6.8.2
/usr/lib/libQt6Svg.so.6.8.2
/usr/lib/libQt6Widgets.so.6.8.2
/usr/lib/libQt6XcbQpa.so.6.8.2
/usr/lib/libX11-xcb.so.1.0.0
/usr/lib/libX11.so.6.4.0
/usr/lib/libXau.so.6.0.0
/usr/lib/libXdmcp.so.6.0.0
/usr/lib/libXext.so.6.4.0
/usr/lib/libXfixes.so.3.1.0
/usr/lib/libXxf86vm.so.1.0.0
/usr/lib/libb2.so.1.0.4
/usr/lib/libblkid.so.1.1.0
/usr/lib/libbrotlicommon.so.1.1.0
/usr/lib/libbrotlidec.so.1.1.0
/usr/lib/libbsd.so.0.12.2
/usr/lib/libbz2.so.1.0.8
/usr/lib/libcares.so.2.19.5
/usr/lib/libcrypto.so.3
/usr/lib/libcurl.so.4.8.0
/usr/lib/libdbus-1.so.3.32.4
/usr/lib/libdouble-conversion.so.3.3.0
/usr/lib/libdrm.so.2.123.0
/usr/lib/libdrm_amdgpu.so.1.123.0
/usr/lib/libdrm_intel.so.1.123.0
/usr/lib/libdrm_radeon.so.1.123.0
/usr/lib/libduktape.so.207.20700
/usr/lib/libeconf.so.0.6.2
/usr/lib/libelf-0.191.so
/usr/lib/libexpat.so.1.11.2
/usr/lib/libffi.so.8.1.4
/usr/lib/libfontconfig.so.1.12.1
/usr/lib/libfreetype.so.6.20.2
/usr/lib/libfribidi.so.0.4.0
/usr/lib/libgallium-24.2.8.so
/usr/lib/libgbm.so.1.0.0
/usr/lib/libgcc_s.so.1
/usr/lib/libgio-2.0.so.0.8200.5
/usr/lib/libglapi.so.0.0.0
/usr/lib/libglib-2.0.so.0.8200.5
/usr/lib/libgmodule-2.0.so.0.8200.5
/usr/lib/libgobject-2.0.so.0.8200.5
/usr/lib/libgomp.so.1.0.0
/usr/lib/libgraphite2.so.3.2.1
/usr/lib/libharfbuzz-subset.so.0.60900.0
/usr/lib/libharfbuzz.so.0.60900.0
/usr/lib/libicudata.so.74.2
/usr/lib/libicui18n.so.74.2
/usr/lib/libicuuc.so.74.2
/usr/lib/libidn2.so.0.4.0
/usr/lib/libimagequant.so.0.0.4
/usr/lib/libintl.so.8.4.0
/usr/lib/libjpeg.so.8.3.2
/usr/lib/liblzma.so.5.6.3
/usr/lib/libmd.so.0.1.0
/usr/lib/libmount.so.1.1.0
/usr/lib/libnghttp2.so.14.28.3
/usr/lib/libopenjp2.so.2.5.2
/usr/lib/libpango-1.0.so.0.5400.0
/usr/lib/libpangoft2-1.0.so.0.5400.0
/usr/lib/libpciaccess.so.0.11.1
/usr/lib/libpcre2-16.so.0.12.0
/usr/lib/libpcre2-8.so.0.12.0
/usr/lib/libpng16.so.16.55.0
/usr/lib/libproxy.so.0.5.9
/usr/lib/libproxy/libpxbackend-1.0.so
/usr/lib/libpsl.so.5.3.5
/usr/lib/libpyside6.abi3.so.6.8.0.2
/usr/lib/libpyside6qml.abi3.so.6.8.0.2
/usr/lib/libpython3.12.so.1.0
/usr/lib/libsharpyuv.so.0.1.0
/usr/lib/libshiboken6.abi3.so.6.8.0.2
/usr/lib/libssl.so.3
/usr/lib/libstdc++.so.6.0.33
/usr/lib/libtiff.so.6.2.0
/usr/lib/libunistring.so.5.1.0
/usr/lib/libwayland-client.so.0.23.1
/usr/lib/libwayland-server.so.0.23.1
/usr/lib/libwebp.so.7.1.9
/usr/lib/libxcb-cursor.so.0.0.0
/usr/lib/libxcb-dri2.so.0.0.0
/usr/lib/libxcb-dri3.so.0.1.0
/usr/lib/libxcb-glx.so.0.0.0
/usr/lib/libxcb-icccm.so.4.0.0
/usr/lib/libxcb-image.so.0.0.0
/usr/lib/libxcb-keysyms.so.1.0.0
/usr/lib/libxcb-present.so.0.0.0
/usr/lib/libxcb-randr.so.0.1.0
/usr/lib/libxcb-render-util.so.0.0.0
/usr/lib/libxcb-render.so.0.0.0
/usr/lib/libxcb-shape.so.0.0.0
/usr/lib/libxcb-shm.so.0.0.0
/usr/lib/libxcb-sync.so.1.0.0
/usr/lib/libxcb-util.so.1.0.0
/usr/lib/libxcb-xfixes.so.0.0.0
/usr/lib/libxcb-xinput.so.0.1.0
/usr/lib/libxcb-xkb.so.1.0.0
/usr/lib/libxcb.so.1.1.0
/usr/lib/libxkbcommon-x11.so.0.0.0
/usr/lib/libxkbcommon.so.0.0.0
/usr/lib/libxml2.so.2.13.9
/usr/lib/libxshmfence.so.1.0.0
/usr/lib/libz.so.1.3.1
/usr/lib/libzstd.so.1.5.6
/usr/lib/python3.12/lib-dynload/_asyncio.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_bisect.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_blake2.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_bz2.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_contextvars.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_ctypes.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_datetime.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_elementtree.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_hashlib.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_heapq.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_json.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_lzma.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_opcode.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_pickle.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_posixsubprocess.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_queue.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_random.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_sha2.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_socket.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_ssl.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/_struct.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/array.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/binascii.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/fcntl.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/math.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/pyexpat.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/resource.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/select.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/syslog.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/termios.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/unicodedata.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/lib-dynload/zlib.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/PIL/_imaging.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/PySide6/QtCore.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtGui.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtNetwork.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtOpenGL.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtQml.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtQuick.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtQuickControls2.abi3.so
/usr/lib/python3.12/site-packages/PySide6/QtWidgets.abi3.so
/usr/lib/python3.12/site-packages/_brotli.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/_cffi_backend.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/evdev/_ecodes.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/evdev/_input.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/evdev/_uinput.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/fontTools/misc/bezierTools.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/fontTools/varLib/iup.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/markupsafe/_speedups.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/msgpack/_cmsgpack.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/psutil/_psutil_linux.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/psutil/_psutil_posix.cpython-312-x86_64-linux-musl.so
/usr/lib/python3.12/site-packages/shiboken6/Shiboken.abi3.so
/usr/lib/qt6/plugins/imageformats/libqgif.so
/usr/lib/qt6/plugins/imageformats/libqico.so
/usr/lib/qt6/plugins/imageformats/libqjpeg.so
/usr/lib/qt6/plugins/imageformats/libqpdf.so
/usr/lib/qt6/plugins/imageformats/libqsvg.so
/usr/lib/qt6/plugins/platforminputcontexts/libcomposeplatforminputcontextplugin.so
/usr/lib/qt6/plugins/platforms/libqxcb.so
/usr/lib/qt6/plugins/xcbglintegrations/libqxcb-glx-integration.so
/usr/lib/qt6/qml/Qt5Compat/GraphicalEffects/libqtgraphicaleffectsplugin.so
/usr/lib/qt6/qml/QtQuick/Controls/Basic/libqtquickcontrols2basicstyleplugin.so
/usr/lib/qt6/qml/QtQuick/Controls/impl/libqtquickcontrols2implplugin.so
/usr/lib/qt6/qml/QtQuick/Controls/libqtquickcontrols2plugin.so
/usr/lib/qt6/qml/QtQuick/Effects/libeffectsplugin.so
/usr/lib/qt6/qml/QtQuick/Layouts/libqquicklayoutsplugin.so
/usr/lib/qt6/qml/QtQuick/Shapes/libqmlshapesplugin.so
/usr/lib/qt6/qml/QtQuick/Templates/libqtquicktemplates2plugin.so
/usr/lib/qt6/qml/QtQuick/Window/libquickwindowplugin.so
```

### Scripts

Identify all libs used:
```
for pid in $(ps -e -o pid=); do
    grep '\.so' /proc/$pid/maps 2>/dev/null
done | awk '{print $6}' | sort -u > /tmp/usedlibs.txt
```