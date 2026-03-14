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

Without `mesa-dri-gallium`:
- RAM used: 389 MB
- Disk used: 1.06 GB

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
/usr/lib/qt6/plugins/xcbglintegrations/libqxcb-egl-integration.so
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

### After truncate-libs:


### Packages installed in `sys-gui`:

```
alpine-base-3.22.3-r0 x86_64 {alpine-base} (MIT) [installed]
alpine-baselayout-3.7.0-r0 x86_64 {alpine-baselayout} (GPL-2.0-only) [installed]
alpine-baselayout-data-3.7.0-r0 x86_64 {alpine-baselayout} (GPL-2.0-only) [installed]
alpine-conf-3.20.0-r1 x86_64 {alpine-conf} (MIT) [installed]
alpine-keys-2.5-r0 x86_64 {alpine-keys} (MIT) [installed]
alpine-release-3.22.3-r0 x86_64 {alpine-base} (MIT) [installed]
alsa-lib-1.2.12-r0 x86_64 {alsa-lib} (LGPL-2.1-or-later) [installed]
aom-libs-3.11.0-r0 x86_64 {aom} (BSD-2-Clause AND custom) [installed]
apk-tools-2.14.9-r3 x86_64 {apk-tools} (GPL-2.0-only) [installed]
assimp-libs-5.4.3-r0 x86_64 {assimp} (BSD-3-Clause) [installed]
at-spi2-core-2.54.1-r0 x86_64 {at-spi2-core} (LGPL-2.1-or-later) [installed]
avahi-libs-0.8-r19 x86_64 {avahi} (LGPL-2.1-or-later) [installed]
bluez-libs-5.79-r0 x86_64 {bluez} (GPL-2.0-or-later AND BSD-2-Clause AND MIT) [installed]
bridge-1.5-r5 x86_64 {bridge} (GPL-2.0-or-later) [installed]
brotli-libs-1.1.0-r2 x86_64 {brotli} (MIT) [installed]
busybox-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
busybox-binsh-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
busybox-mdev-openrc-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
busybox-openrc-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
busybox-suid-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
c-ares-1.34.6-r0 x86_64 {c-ares} (MIT) [installed]
ca-certificates-bundle-20250911-r0 x86_64 {ca-certificates} (MPL-2.0 AND MIT) [installed]
cairo-1.18.4-r0 x86_64 {cairo} (LGPL-2.1-or-later OR MPL-1.1) [installed]
cairo-gobject-1.18.4-r0 x86_64 {cairo} (LGPL-2.1-or-later OR MPL-1.1) [installed]
cjson-1.7.19-r0 x86_64 {cjson} (MIT) [installed]
clang19-headers-19.1.4-r0 x86_64 {clang19} (Apache-2.0 WITH LLVM-exception) [installed]
clang19-libclang-19.1.4-r0 x86_64 {clang19} (Apache-2.0 WITH LLVM-exception) [installed]
cups-libs-2.4.16-r0 x86_64 {cups} (Apache-2.0) [installed]
dbus-libs-1.14.10-r4 x86_64 {dbus} (AFL-2.1 OR GPL-2.0-or-later) [installed]
dmidecode-3.6-r0 x86_64 {dmidecode} (GPL-2.0-or-later) [installed]
double-conversion-3.3.0-r0 x86_64 {double-conversion} (BSD-3-Clause) [installed]
duktape-2.7.0-r1 x86_64 {duktape} (MIT) [installed]
encodings-1.0.7-r1 noarch {encodings} (Public Domain) [installed]
eudev-3.2.14-r5 x86_64 {eudev} (GPL-2.0-or-later) [installed]
eudev-libs-3.2.14-r5 x86_64 {eudev} (GPL-2.0-or-later) [installed]
eudev-openrc-3.2.14-r5 noarch {eudev} (GPL-2.0-or-later) [installed]
ffmpeg-libavcodec-6.1.2-r1 x86_64 {ffmpeg} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
ffmpeg-libavformat-6.1.2-r1 x86_64 {ffmpeg} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
ffmpeg-libavutil-6.1.2-r1 x86_64 {ffmpeg} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
ffmpeg-libswresample-6.1.2-r1 x86_64 {ffmpeg} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
ffmpeg-libswscale-6.1.2-r1 x86_64 {ffmpeg} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
file-5.46-r2 x86_64 {file} (BSD-2-Clause) [installed]
flite-2.2-r3 x86_64 {flite} (BSD-4-Clause) [installed]
font-alias-1.0.5-r0 noarch {font-alias} (custom) [installed]
font-cursor-misc-1.0.4-r1 noarch {font-cursor-misc} (Public Domain) [installed]
font-misc-misc-1.1.3-r1 noarch {font-misc-misc} (Public Domain) [installed]
font-roboto-3.005-r0 noarch {font-roboto} (Apache-2.0) [installed]
fontconfig-2.15.0-r1 x86_64 {fontconfig} (MIT) [installed]
freetype-2.13.3-r0 x86_64 {freetype} (FTL OR GPL-2.0-or-later) [installed]
fribidi-1.0.16-r0 x86_64 {fribidi} (LGPL-2.1-or-later) [installed]
gdbm-1.24-r0 x86_64 {gdbm} (GPL-3.0-or-later) [installed]
gdk-pixbuf-2.42.12-r1 x86_64 {gdk-pixbuf} (LGPL-2.1-or-later) [installed]
giflib-5.2.2-r1 x86_64 {giflib} (MIT) [installed]
glib-2.82.5-r0 x86_64 {glib} (LGPL-2.1-or-later) [installed]
gmp-6.3.0-r2 x86_64 {gmp} (LGPL-3.0-or-later OR GPL-2.0-or-later) [installed]
gnutls-3.8.12-r0 x86_64 {gnutls} (LGPL-2.1-or-later) [installed]
graphite2-1.3.14-r6 x86_64 {graphite2} (LGPL-2.1-or-later OR MPL-1.1) [installed]
gtk+3.0-3.24.49-r0 x86_64 {gtk+3.0} (LGPL-2.1-or-later) [installed]
gtk-update-icon-cache-3.24.49-r0 x86_64 {gtk+3.0} (LGPL-2.1-or-later) [installed]
harfbuzz-9.0.0-r1 x86_64 {harfbuzz} (MIT) [installed]
harfbuzz-subset-9.0.0-r1 x86_64 {harfbuzz} (MIT) [installed]
hicolor-icon-theme-0.18-r0 noarch {hicolor-icon-theme} (GPL-2.0-or-later) [installed]
hwdata-pci-0.393-r0 noarch {hwdata} (GPL-2.0-or-later OR XFree86-1.1) [installed]
icu-data-full-74.2-r1 noarch {icu} (ICU) [installed]
icu-libs-74.2-r1 x86_64 {icu} (ICU) [installed]
ifupdown-ng-0.12.1-r7 x86_64 {ifupdown-ng} (ISC) [installed]
imath-3.1.12-r0 x86_64 {imath} (BSD-3-Clause) [installed]
kmod-libs-33-r2 x86_64 {kmod} (LGPL-2.1-or-later) [installed]
lame-libs-3.100-r5 x86_64 {lame} (LGPL-2.0-or-later) [installed]
lcms2-2.16-r0 x86_64 {lcms2} (MIT) [installed]
libapk2-2.14.9-r3 x86_64 {apk-tools} (GPL-2.0-only) [installed]
libasyncns-0.8-r4 x86_64 {libasyncns} (LGPL-2.0-or-later) [installed]
libatk-1.0-2.54.1-r0 x86_64 {at-spi2-core} (LGPL-2.1-or-later) [installed]
libatk-bridge-2.0-2.54.1-r0 x86_64 {at-spi2-core} (LGPL-2.1-or-later) [installed]
libb2-0.98.1-r3 x86_64 {libb2} (CC0-1.0) [installed]
libblkid-2.40.4-r1 x86_64 {util-linux} (LGPL-2.1-or-later) [installed]
libbluray-1.3.4-r1 x86_64 {libbluray} (LGPL-2.1-or-later) [installed]
libbsd-0.12.2-r0 x86_64 {libbsd} (BSD-3-Clause) [installed]
libbz2-1.0.8-r6 x86_64 {bzip2} (bzip2-1.0.6) [installed]
libcap2-2.76-r0 x86_64 {libcap} (BSD-3-Clause OR GPL-2.0-only) [installed]
libcrypto3-3.5.5-r0 x86_64 {openssl} (Apache-2.0) [installed]
libcurl-8.14.1-r2 x86_64 {curl} (curl) [installed]
libdav1d-1.5.0-r0 x86_64 {dav1d} (BSD-2-Clause) [installed]
libdeflate-1.22-r0 x86_64 {libdeflate} (MIT) [installed]
libdrm-2.4.123-r1 x86_64 {libdrm} (MIT) [installed]
libeconf-0.6.3-r0 x86_64 {libeconf} (MIT) [installed]
libelf-0.191-r0 x86_64 {elfutils} (GPL-3.0-or-later AND ( GPL-2.0-or-later OR LGPL-3.0-or-later )) [installed]
libepoxy-1.5.10-r1 x86_64 {libepoxy} (MIT) [installed]
libevdev-1.13.3-r0 x86_64 {libevdev} (MIT) [installed]
libevent-2.1.12-r7 x86_64 {libevent} (BSD-3-Clause) [installed]
libexpat-2.7.4-r0 x86_64 {expat} (MIT) [installed]
libffi-3.4.7-r0 x86_64 {libffi} (MIT) [installed]
libflac-1.4.3-r1 x86_64 {flac} (BSD-3-Clause AND GPL-2.0-or-later) [installed]
libfontenc-1.1.8-r0 x86_64 {libfontenc} (MIT) [installed]
libgcc-14.2.0-r4 x86_64 {gcc} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
libgcrypt-1.10.3-r1 x86_64 {libgcrypt} (LGPL-2.1-or-later AND GPL-2.0-or-later) [installed]
libgomp-14.2.0-r4 x86_64 {gcc} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
libgpg-error-1.51-r0 x86_64 {libgpg-error} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
libhwy-1.0.7-r0 x86_64 {highway} (Apache-2.0) [installed]
libice-1.1.1-r6 x86_64 {libice} (X11) [installed]
libidn2-2.3.7-r0 x86_64 {libidn2} (GPL-2.0-or-later OR LGPL-3.0-or-later) [installed]
libimagequant-4.2.2-r0 x86_64 {libimagequant} (GPL-3.0-or-later) [installed]
libinput-libs-1.27.0-r0 x86_64 {libinput} (MIT) [installed]
libinput-udev-1.27.0-r0 x86_64 {libinput} (MIT) [installed]
libintl-0.22.5-r0 x86_64 {gettext} (LGPL-2.1-or-later) [installed]
libjpeg-turbo-3.0.4-r0 x86_64 {libjpeg-turbo} (BSD-3-Clause AND IJG AND Zlib) [installed]
libjxl-0.10.4-r0 x86_64 {libjxl} (Apache-2.0) [installed]
libltdl-2.4.7-r3 x86_64 {libtool} (LGPL-2.0-or-later AND GPL-2.0-or-later) [installed]
libmagic-5.46-r2 x86_64 {file} (BSD-2-Clause) [installed]
libmd-1.1.0-r0 x86_64 {libmd} (BSD-3-Clause AND BSD-2-Clause AND ISC AND Beerware AND Public Domain) [installed]
libmount-2.40.4-r1 x86_64 {util-linux} (LGPL-2.1-or-later) [installed]
libncursesw-6.5_p20241006-r3 x86_64 {ncurses} (X11) [installed]
libogg-1.3.5-r5 x86_64 {libogg} (BSD-3-Clause) [installed]
libopenmpt-0.7.12-r0 x86_64 {libopenmpt} (BSD-3-Clause) [installed]
libpanelw-6.5_p20241006-r3 x86_64 {ncurses} (X11) [installed]
libpciaccess-0.18.1-r0 x86_64 {libpciaccess} (X11) [installed]
libpcre2-16-10.43-r0 x86_64 {pcre2} (BSD-3-Clause) [installed]
libpng-1.6.55-r0 x86_64 {libpng} (Libpng) [installed]
libproxy-0.5.9-r0 x86_64 {libproxy} (LGPL-2.0-or-later) [installed]
libpsl-0.21.5-r3 x86_64 {libpsl} (MIT) [installed]
libpulse-17.0-r4 x86_64 {pulseaudio} (LGPL-2.1-or-later) [installed]
librist-0.2.10-r1 x86_64 {librist} (BSD-2-Clause) [installed]
libsharpyuv-1.4.0-r0 x86_64 {libwebp} (BSD-3-Clause) [installed]
libsm-1.2.4-r4 x86_64 {libsm} (MIT) [installed]
libsndfile-1.2.2-r2 x86_64 {libsndfile} (LGPL-2.1-or-later) [installed]
libsodium-1.0.20-r1 x86_64 {libsodium} (ISC) [installed]
libsrt-1.5.3-r0 x86_64 {libsrt} (MPL-2.0) [installed]
libssh-0.11.1-r0 x86_64 {libssh} (LGPL-2.1-or-later BSD-2-Clause) [installed]
libssl3-3.5.5-r0 x86_64 {openssl} (Apache-2.0) [installed]
libstdc++-14.2.0-r4 x86_64 {gcc} (GPL-2.0-or-later AND LGPL-2.1-or-later) [installed]
libSvtAv1Enc-2.2.1-r0 x86_64 {svt-av1} (BSD-3-Clause-Clear) [installed]
libtasn1-4.21.0-r0 x86_64 {libtasn1} (LGPL-2.1-or-later) [installed]
libtheora-1.1.1-r18 x86_64 {libtheora} (BSD-3-Clause) [installed]
libunistring-1.2-r0 x86_64 {libunistring} (GPL-2.0-or-later OR LGPL-3.0-or-later) [installed]
libuuid-2.40.4-r1 x86_64 {util-linux} (BSD-3-Clause) [installed]
libva-2.22.0-r1 x86_64 {libva} (MIT) [installed]
libvdpau-1.5-r4 x86_64 {libvdpau} (MIT) [installed]
libvorbis-1.3.7-r2 x86_64 {libvorbis} (BSD-3-Clause) [installed]
libvpx-1.15.0-r0 x86_64 {libvpx} (BSD-3-Clause) [installed]
libwebp-1.4.0-r0 x86_64 {libwebp} (BSD-3-Clause) [installed]
libwebpdemux-1.4.0-r0 x86_64 {libwebp} (BSD-3-Clause) [installed]
libwebpmux-1.4.0-r0 x86_64 {libwebp} (BSD-3-Clause) [installed]
libx11-1.8.10-r0 x86_64 {libx11} (X11) [installed]
libxau-1.0.11-r4 x86_64 {libxau} (MIT) [installed]
libxcb-1.16.1-r0 x86_64 {libxcb} (MIT) [installed]
libxcomposite-0.4.6-r5 x86_64 {libxcomposite} (MIT) [installed]
libxcursor-1.2.3-r0 x86_64 {libxcursor} (MIT) [installed]
libxcvt-0.1.2-r0 x86_64 {libxcvt} (custom) [installed]
libxdamage-1.1.6-r5 x86_64 {libxdamage} (MIT) [installed]
libxdmcp-1.1.5-r1 x86_64 {libxdmcp} (MIT) [installed]
libxext-1.3.6-r2 x86_64 {libxext} (MIT) [installed]
libxfixes-6.0.1-r4 x86_64 {libxfixes} (MIT) [installed]
libxfont2-2.0.7-r0 x86_64 {libxfont2} (MIT) [installed]
libxft-2.3.8-r3 x86_64 {libxft} (MIT) [installed]
libxi-1.8.2-r0 x86_64 {libxi} (MIT AND X11) [installed]
libxinerama-1.1.5-r4 x86_64 {libxinerama} (MIT) [installed]
libxkbcommon-1.7.0-r1 x86_64 {libxkbcommon} (MIT) [installed]
libxkbcommon-x11-1.7.0-r1 x86_64 {libxkbcommon} (MIT) [installed]
libxkbfile-1.1.3-r0 x86_64 {libxkbfile} (MIT) [installed]
libxml2-2.13.9-r0 x86_64 {libxml2} (MIT) [installed]
libxmu-1.2.1-r0 x86_64 {libxmu} (MIT) [installed]
libxrandr-1.5.4-r1 x86_64 {libxrandr} (MIT) [installed]
libxrender-0.9.11-r5 x86_64 {libxrender} (MIT) [installed]
libxshmfence-1.3.2-r6 x86_64 {libxshmfence} (MIT) [installed]
libxslt-1.1.42-r2 x86_64 {libxslt} (X11) [installed]
libxt-1.3.1-r0 x86_64 {libxt} (MIT) [installed]
libxtst-1.2.5-r0 x86_64 {libxtst} (MIT) [installed]
libxxf86vm-1.1.5-r6 x86_64 {libxxf86vm} (MIT) [installed]
libzmq-4.3.5-r2 x86_64 {zeromq} (MPL-2.0) [installed]
llvm19-libs-19.1.4-r1 x86_64 {llvm19} (Apache-2.0) [installed]
mbedtls-3.6.5-r0 x86_64 {mbedtls} (Apache-2.0 OR GPL-2.0-or-later) [installed]
mdev-conf-4.8-r0 x86_64 {mdev-conf} (MIT) [installed]
mesa-24.2.8-r0 x86_64 {mesa} (MIT AND SGI-B-2.0 AND BSL-1.0) [installed]
mesa-egl-24.2.8-r0 x86_64 {mesa} (MIT AND SGI-B-2.0 AND BSL-1.0) [installed]
mesa-gbm-24.2.8-r0 x86_64 {mesa} (MIT AND SGI-B-2.0 AND BSL-1.0) [installed]
mesa-gl-24.2.8-r0 x86_64 {mesa} (MIT AND SGI-B-2.0 AND BSL-1.0) [installed]
mesa-glapi-24.2.8-r0 x86_64 {mesa} (MIT AND SGI-B-2.0 AND BSL-1.0) [installed]
minizip-1.3.1-r0 x86_64 {minizip} (Zlib) [installed]
mkfontscale-1.2.3-r1 x86_64 {mkfontscale} (MIT) [installed]
mpdecimal-4.0.0-r0 x86_64 {mpdecimal} (BSD-2-Clause) [installed]
mpg123-libs-1.32.9-r0 x86_64 {mpg123} (LGPL-2.1-only) [installed]
mtdev-1.1.7-r0 x86_64 {mtdev} (MIT) [installed]
musl-1.2.5-r10 x86_64 {musl} (MIT) [installed]
musl-utils-1.2.5-r10 x86_64 {musl} (MIT AND BSD-2-Clause AND GPL-2.0-or-later) [installed]
ncdu-1.21-r0 x86_64 {ncdu} (MIT) [installed]
ncurses-terminfo-base-6.5_p20241006-r3 noarch {ncurses} (X11) [installed]
nettle-3.10.2-r0 x86_64 {nettle} (GPL-2.0-or-later OR LGPL-3.0-or-later) [installed]
nghttp2-libs-1.64.0-r0 x86_64 {nghttp2} (MIT) [installed]
nspr-4.36-r0 x86_64 {nspr} (MPL-2.0) [installed]
nss-3.109-r0 x86_64 {nss} (MPL-2.0) [installed]
numactl-2.0.18-r0 x86_64 {numactl} (LGPL-2.1-only) [installed]
onevpl-libs-2023.3.1-r2 x86_64 {onevpl} (MIT) [installed]
openexr-libiex-3.3.2-r0 x86_64 {openexr} (BSD-3-Clause) [installed]
openexr-libilmthread-3.3.2-r0 x86_64 {openexr} (BSD-3-Clause) [installed]
openexr-libopenexr-3.3.2-r0 x86_64 {openexr} (BSD-3-Clause) [installed]
openexr-libopenexrcore-3.3.2-r0 x86_64 {openexr} (BSD-3-Clause) [installed]
openjpeg-2.5.2-r0 x86_64 {openjpeg} (BSD-2-Clause) [installed]
openrc-0.62.6-r0 x86_64 {openrc} (BSD-2-Clause) [installed]
openrc-user-0.62.6-r0 x86_64 {openrc} (BSD-2-Clause) [installed]
openssl-3.5.5-r0 x86_64 {openssl} (Apache-2.0) [installed]
openxr-1.1.43-r0 x86_64 {openxr} (Apache-2.0) [installed]
opus-1.5.2-r1 x86_64 {opus} (BSD-3-Clause) [installed]
orc-0.4.40-r1 x86_64 {orc} (BSD-2-Clause) [installed]
p11-kit-0.25.5-r2 x86_64 {p11-kit} (BSD-3-Clause) [installed]
pango-1.54.0-r1 x86_64 {pango} (LGPL-2.1-or-later) [installed]
pcre2-10.43-r0 x86_64 {pcre2} (BSD-3-Clause) [installed]
pixman-0.43.4-r1 x86_64 {pixman} (MIT) [installed]
pkgconf-2.3.0-r0 x86_64 {pkgconf} (ISC) [installed]
py3-brotli-1.1.0-r2 x86_64 {brotli} (MIT) [installed]
py3-brotli-pyc-1.1.0-r2 noarch {brotli} (MIT) [installed]
py3-cffi-1.17.1-r1 x86_64 {py3-cffi} (MIT) [installed]
py3-cffi-pyc-1.17.1-r1 noarch {py3-cffi} (MIT) [installed]
py3-cparser-2.22-r1 noarch {py3-cparser} (BSD-3-Clause) [installed]
py3-cparser-pyc-2.22-r1 noarch {py3-cparser} (BSD-3-Clause) [installed]
py3-cssselect2-0.7.0-r5 noarch {py3-cssselect2} (BSD-3-Clause) [installed]
py3-cssselect2-pyc-0.7.0-r5 noarch {py3-cssselect2} (BSD-3-Clause) [installed]
py3-evdev-1.7.1-r0 x86_64 {py3-evdev} (BSD-3-Clause) [installed]
py3-evdev-pyc-1.7.1-r0 noarch {py3-evdev} (BSD-3-Clause) [installed]
py3-fonttools-4.55.0-r0 x86_64 {py3-fonttools} (MIT AND OFL-1.1) [installed]
py3-fonttools-pyc-4.55.0-r0 noarch {py3-fonttools} (MIT AND OFL-1.1) [installed]
py3-humanize-4.9.0-r1 noarch {py3-humanize} (MIT) [installed]
py3-humanize-pyc-4.9.0-r1 noarch {py3-humanize} (MIT) [installed]
py3-inotify-simple-1.3.5-r2 noarch {py3-inotify-simple} (BSD-2-Clause) [installed]
py3-inotify-simple-pyc-1.3.5-r2 noarch {py3-inotify-simple} (BSD-2-Clause) [installed]
py3-jinja2-3.1.6-r0 noarch {py3-jinja2} (BSD-3-Clause) [installed]
py3-jinja2-pyc-3.1.6-r0 noarch {py3-jinja2} (BSD-3-Clause) [installed]
py3-markupsafe-3.0.2-r0 x86_64 {py3-markupsafe} (BSD-3-Clause) [installed]
py3-markupsafe-pyc-3.0.2-r0 noarch {py3-markupsafe} (BSD-3-Clause) [installed]
py3-msgpack-1.0.8-r1 x86_64 {py3-msgpack} (Apache-2.0) [installed]
py3-msgpack-pyc-1.0.8-r1 noarch {py3-msgpack} (Apache-2.0) [installed]
py3-paho-mqtt2-2.1.0-r3 noarch {py3-paho-mqtt2} (EPL-1.0) [installed]
py3-paho-mqtt2-pyc-2.1.0-r3 noarch {py3-paho-mqtt2} (EPL-1.0) [installed]
py3-pillow-11.0.0-r0 x86_64 {py3-pillow} (custom:PIL) [installed]
py3-pillow-pyc-11.0.0-r0 noarch {py3-pillow} (custom:PIL) [installed]
py3-psutil-6.0.0-r0 x86_64 {py3-psutil} (BSD-3-Clause) [installed]
py3-psutil-pyc-6.0.0-r0 noarch {py3-psutil} (BSD-3-Clause) [installed]
py3-pydyf-0.11.0-r0 noarch {py3-pydyf} (BSD-3-Clause) [installed]
py3-pydyf-pyc-0.11.0-r0 noarch {py3-pydyf} (BSD-3-Clause) [installed]
py3-pyphen-0.17.0-r0 noarch {py3-pyphen} (GPL-2.0-or-later AND LGPL-2.1-or-later AND MPL-1.1) [installed]
py3-pyphen-pyc-0.17.0-r0 noarch {py3-pyphen} (GPL-2.0-or-later AND LGPL-2.1-or-later AND MPL-1.1) [installed]
py3-pyserial-3.5-r7 noarch {py3-pyserial} (BSD-3-Clause) [installed]
py3-pyserial-pyc-3.5-r7 noarch {py3-pyserial} (BSD-3-Clause) [installed]
py3-pyside6-6.8.0.2-r1 x86_64 {pyside6} (LGPL-3.0-only AND GPL-2.0-only) [installed]
py3-shiboken6-6.8.0.2-r1 x86_64 {pyside6} (LGPL-3.0-only AND GPL-2.0-only) [installed]
py3-tinycss2-1.4.0-r0 noarch {py3-tinycss2} (BSD-3-Clause) [installed]
py3-tinycss2-pyc-1.4.0-r0 noarch {py3-tinycss2} (BSD-3-Clause) [installed]
py3-tinyhtml5-2.0.0-r0 x86_64 {py3-tinyhtml5} (MIT) [installed]
py3-tinyhtml5-pyc-2.0.0-r0 noarch {py3-tinyhtml5} (MIT) [installed]
py3-udev-0.24.1-r2 noarch {py3-udev} (LGPL-2.1-or-later) [installed]
py3-udev-pyc-0.24.1-r2 noarch {py3-udev} (LGPL-2.1-or-later) [installed]
py3-webencodings-0.5.1-r8 noarch {py3-webencodings} (MIT) [installed]
py3-webencodings-pyc-0.5.1-r8 noarch {py3-webencodings} (MIT) [installed]
py3-zopfli-0.2.3-r2 x86_64 {py3-zopfli} (Apache-2.0) [installed]
py3-zopfli-pyc-0.2.3-r2 noarch {py3-zopfli} (Apache-2.0) [installed]
pyc-3.12.12-r0 noarch {python3} (PSF-2.0) [installed]
python3-3.12.12-r0 x86_64 {python3} (PSF-2.0) [installed]
python3-pyc-3.12.12-r0 noarch {python3} (PSF-2.0) [installed]
python3-pycache-pyc0-3.12.12-r0 x86_64 {python3} (PSF-2.0) [installed]
qt6-qt3d-6.8.2-r0 x86_64 {qt6-qt3d} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qt5compat-6.8.2-r0 x86_64 {qt6-qt5compat} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtbase-6.8.2-r0 x86_64 {qt6-qtbase} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtbase-x11-6.8.2-r0 x86_64 {qt6-qtbase} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtcharts-6.8.2-r0 x86_64 {qt6-qtcharts} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtconnectivity-6.8.2-r0 x86_64 {qt6-qtconnectivity} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtdatavis3d-6.8.2-r0 x86_64 {qt6-qtdatavis3d} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtdeclarative-6.8.2-r0 x86_64 {qt6-qtdeclarative} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qthttpserver-6.8.2-r0 x86_64 {qt6-qthttpserver} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtmultimedia-6.8.2-r0 x86_64 {qt6-qtmultimedia} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtmultimedia-ffmpeg-6.8.2-r0 x86_64 {qt6-qtmultimedia} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtnetworkauth-6.8.2-r0 x86_64 {qt6-qtnetworkauth} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtpositioning-6.8.2-r0 x86_64 {qt6-qtpositioning} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtquick3d-6.8.2-r0 x86_64 {qt6-qtquick3d} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtquicktimeline-6.8.2-r0 x86_64 {qt6-qtquicktimeline} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtremoteobjects-6.8.2-r0 x86_64 {qt6-qtremoteobjects} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtscxml-6.8.2-r0 x86_64 {qt6-qtscxml} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtsensors-6.8.2-r0 x86_64 {qt6-qtsensors} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtserialport-6.8.2-r0 x86_64 {qt6-qtserialport} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtshadertools-6.8.2-r0 x86_64 {qt6-qtshadertools} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtspeech-6.8.2-r0 x86_64 {qt6-qtspeech} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtsvg-6.8.2-r0 x86_64 {qt6-qtsvg} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qttools-libs-6.8.2-r0 x86_64 {qt6-qttools} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtwayland-6.8.2-r0 x86_64 {qt6-qtwayland} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtwebchannel-6.8.2-r0 x86_64 {qt6-qtwebchannel} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtwebengine-6.8.2-r0 x86_64 {qt6-qtwebengine} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
qt6-qtwebsockets-libs-6.8.2-r0 x86_64 {qt6-qtwebsockets} (LGPL-2.1-only AND LGPL-3.0-only AND GPL-3.0-only AND Qt-GPL-exception-1.0) [installed]
rav1e-libs-0.7.1-r0 x86_64 {rav1e} (BSD-2-Clause custom) [installed]
readline-8.2.13-r0 x86_64 {readline} (GPL-3.0-or-later) [installed]
safecor-gui-base-1.2-r1 noarch {safecor-gui-base} (MIT) [installed]
safecor-lib-1.2-r0 noarch {safecor-lib} (MIT) [installed]
saphir-gui-3.0-r1 noarch {saphir-gui} (MIT) [installed]
saphir-lib-1.0-r0 noarch {saphir-lib} (MIT) [installed]
scanelf-1.3.8-r1 x86_64 {pax-utils} (GPL-2.0-only) [installed]
shared-mime-info-2.4-r2 x86_64 {shared-mime-info} (GPL-2.0-or-later) [installed]
snappy-1.1.10-r2 x86_64 {snappy} (BSD-3-Clause) [installed]
soxr-0.1.3-r7 x86_64 {soxr} (LGPL-2.1-or-later) [installed]
speexdsp-1.2.1-r2 x86_64 {speexdsp} (BSD-3-Clause) [installed]
sqlite-libs-3.48.0-r4 x86_64 {sqlite} (blessing) [installed]
ssl_client-1.37.0-r20 x86_64 {busybox} (GPL-2.0-only) [installed]
tdb-libs-1.4.12-r0 x86_64 {tdb} (LGPL-3.0-or-later) [installed]
tiff-4.7.1-r0 x86_64 {tiff} (libtiff) [installed]
tslib-1.23-r0 x86_64 {tslib} (LGPL-2.0-or-later) [installed]
tzdata-2026a-r0 x86_64 {tzdata} (Public-Domain) [installed]
udev-init-scripts-35-r1 noarch {udev-init-scripts} (GPL-2.0-only) [installed]
udev-init-scripts-openrc-35-r1 noarch {udev-init-scripts} (GPL-2.0-only) [installed]
util-macros-1.20.1-r0 noarch {util-macros} (MIT) [installed]
wayland-libs-client-1.23.1-r0 x86_64 {wayland} (MIT) [installed]
wayland-libs-cursor-1.23.1-r0 x86_64 {wayland} (MIT) [installed]
wayland-libs-egl-1.23.1-r0 x86_64 {wayland} (MIT) [installed]
wayland-libs-server-1.23.1-r0 x86_64 {wayland} (MIT) [installed]
weasyprint-63.0-r0 noarch {weasyprint} (BSD-3-Clause) [installed]
weasyprint-pyc-63.0-r0 noarch {weasyprint} (BSD-3-Clause) [installed]
x264-libs-0.164.3108-r0 x86_64 {x264} (GPL-2.0-or-later) [installed]
x265-libs-3.6-r0 x86_64 {x265} (GPL-2.0-or-later) [installed]
xcb-util-0.4.1-r3 x86_64 {xcb-util} (MIT) [installed]
xcb-util-cursor-0.1.5-r0 x86_64 {xcb-util-cursor} (MIT) [installed]
xcb-util-image-0.4.1-r0 x86_64 {xcb-util-image} (MIT) [installed]
xcb-util-keysyms-0.4.1-r0 x86_64 {xcb-util-keysyms} (MIT) [installed]
xcb-util-renderutil-0.3.10-r0 x86_64 {xcb-util-renderutil} (MIT) [installed]
xcb-util-wm-0.4.2-r0 x86_64 {xcb-util-wm} (MIT) [installed]
xdg-utils-1.2.1-r1 noarch {xdg-utils} (MIT) [installed]
xdpyinfo-1.3.4-r1 x86_64 {xdpyinfo} (custom) [installed]
xe-guest-utilities-8.4.0-r5 x86_64 {xe-guest-utilities} (BSD-2-Clause) [installed]
xe-guest-utilities-udev-8.4.0-r5 noarch {xe-guest-utilities} (BSD-2-Clause) [installed]
xf86-input-libinput-1.5.0-r0 x86_64 {xf86-input-libinput} (MIT) [installed]
xkbcomp-1.5.0-r0 x86_64 {xkbcomp} (MIT) [installed]
xkeyboard-config-2.43-r0 noarch {xkeyboard-config} (MIT) [installed]
xorg-server-21.1.16-r0 x86_64 {xorg-server} (MIT) [installed]
xorg-server-common-21.1.16-r0 noarch {xorg-server} (MIT) [installed]
xprop-1.2.8-r0 x86_64 {xprop} (MIT) [installed]
xrandr-1.5.2-r0 x86_64 {xrandr} (MIT) [installed]
xset-1.2.5-r1 x86_64 {xset} (MIT) [installed]
xsetroot-1.1.3-r1 x86_64 {xsetroot} (MIT) [installed]
xvidcore-1.3.7-r2 x86_64 {xvidcore} (GPL-2.0-or-later) [installed]
xz-libs-5.6.3-r1 x86_64 {xz} (GPL-2.0-or-later AND 0BSD AND Public-Domain AND LGPL-2.1-or-later) [installed]
zlib-1.3.1-r2 x86_64 {zlib} (Zlib) [installed]
zopfli-1.0.3-r3 x86_64 {zopfli} (Apache-2.0) [installed]
zstd-libs-1.5.6-r2 x86_64 {zstd} (BSD-3-Clause OR GPL-2.0-or-later) [installed]
```

### Scripts

Identify all libs used:

```
for pid in $(ps -e -o pid=); do
    grep '\.so' /proc/$pid/maps 2>/dev/null
done | awk '{print $6}' | sort -u > /tmp/usedlibs.txt
```

Remove all libs used:

```
while IFS= read -r line; do
	echo "Removing file: $line"
done < files.txt
```