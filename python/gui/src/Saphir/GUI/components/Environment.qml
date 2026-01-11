pragma Singleton
import QtQuick
import Components
import Themes

QtObject {
    id: root

    property bool handheld: false
    property bool portrait: false

    property int theme: Constants.dark

    property int mainWidth: 1200
    property int mainHeight: 800    

    /** Colors */
    property color colorDark: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorDark;
            case Constants.dark: return ThemeDark.colorDark;
        }
    }

    property color colorClear: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorClear;
            case Constants.dark: return ThemeDark.colorClear;
        }
    }

    property color colorControl: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorControl;
            case Constants.dark: return ThemeDark.colorControl;
        }
    }

    property color colorText: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorText;
            case Constants.dark: return ThemeDark.colorText;
        }
    }

    property color colorBorder: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorBorder;
            case Constants.dark: return ThemeDark.colorBorder;
        }
    }

    property color colorBg: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorBg;
            case Constants.dark: return ThemeDark.colorBg;
        }
    }

    property color colorButtonEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonEnabled;
            case Constants.dark: return ThemeDark.colorButtonEnabled;
        }
    }

    property color colorButtonDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonDisabled;
            case Constants.dark: return ThemeDark.colorButtonDisabled;
        }
    }

    property color colorShadowEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorShadowEnabled;
            case Constants.dark: return ThemeDark.colorShadowEnabled;
        }
    }

    property color colorShadowDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorShadowDisabled;
            case Constants.dark: return ThemeDark.colorShadowDisabled;
        }
    }

    property color colorButtonTextEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonTextEnabled;
            case Constants.dark: return ThemeDark.colorButtonTextEnabled;
        }
    }

    property color colorButtonTextDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonTextDisabled;
            case Constants.dark: return ThemeDark.colorButtonTextDisabled;
        }
    }

    property color colorPanelEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorPanelEnabled;
            case Constants.dark: return ThemeDark.colorPanelEnabled;
        }
    }

    property color colorPanelDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorPanelDisabled;
            case Constants.dark: return ThemeDark.colorPanelDisabled;
        }
    }

    property color colorFilterNotReady: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterNotReady;
            case Constants.dark: return ThemeDark.colorFilterNotReady;
        }
    }

    property color colorFilterReady: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterReady;
            case Constants.dark: return ThemeDark.colorFilterReady;
        }
    }

    property color colorFilterUsed: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterUsed;
            case Constants.dark: return ThemeDark.colorFilterUsed;
        }
    }

    property color colorFilterInfected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterInfected;
            case Constants.dark: return ThemeDark.colorFilterInfected;
        }
    }

    property color colorClean: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorClean;
            case Constants.dark: return ThemeDark.colorClean;
        }
    }

    property color colorInfected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorInfected;
            case Constants.dark: return ThemeDark.colorInfected;
        }
    }

    property color colorWaiting: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorWaiting;
            case Constants.dark: return ThemeDark.colorWaiting;
        }
    }

    property color colorSelected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorSelected;
            case Constants.dark: return ThemeDark.colorSelected;
        }
    }

}
