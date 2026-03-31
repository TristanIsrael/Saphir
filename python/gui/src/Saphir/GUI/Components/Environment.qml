pragma Singleton
import QtQuick
import QtQuick.Window
import Components
import Themes
import Saphir

QtObject {
    id: root

    property bool handheld: ApplicationController.handheld
    property bool portrait: false

    property int theme: Constants.dark    

    property int mainWidth: 1200
    property int mainHeight: 800

    /** Images */
    property string backgroundImage: {
        switch(root.theme) {
            case Constants.dark: return "images/dark.jpg"
            case Constants.light: return "images/light.jpg"
            case Constants.lowVisibility: return "images/dark.jpg"
        }
    }

    property string systemReadyImage: {
        switch(root.theme) {
            case Constants.dark: return "images/dark.jpg"
            case Constants.light: return "images/light_ready.png"
            case Constants.lowVisibility: return "images/dark.jpg"
        }
    }

    property string systemUsedImage: {
        switch(root.theme) {
            case Constants.dark: return "images/dark.jpg"
            case Constants.light: return "images/light_used.png"
            case Constants.lowVisibility: return "images/dark.jpg"
        }
    }

    property string systemInfectedImage: {
        switch(root.theme) {
            case Constants.dark: return "images/dark.jpg"
            case Constants.light: return "images/light_infected.png"
            case Constants.lowVisibility: return "images/dark.jpg"
        }
    }

    /** Colors */
    property color colorOverlay: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorOverlay;
            case Constants.dark: return ThemeDark.colorOverlay;
            case Constants.light: return ThemeLight.colorOverlay;
            case Constants.lowVisibility: return ThemeLowVisibility.colorOverlay;
        }
    }

    property color colorDark: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorDark;
            case Constants.dark: return ThemeDark.colorDark;
            case Constants.light: return ThemeLight.colorDark;
            case Constants.lowVisibility: return ThemeLowVisibility.colorDark;
        }
    }

    property color colorClear: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorClear;
            case Constants.dark: return ThemeDark.colorClear;
            case Constants.light: return ThemeLight.colorClear;
            case Constants.lowVisibility: return ThemeLowVisibility.colorClear;
        }
    }

    property color colorControl: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorControl;
            case Constants.dark: return ThemeDark.colorControl;
            case Constants.light: return ThemeLight.colorControl;
            case Constants.lowVisibility: return ThemeLowVisibility.colorControl;
        }
    }

    property color colorText: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorText;
            case Constants.dark: return ThemeDark.colorText;
            case Constants.light: return ThemeLight.colorText;
            case Constants.lowVisibility: return ThemeLowVisibility.colorText;
        }
    }

    property color colorBorder: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorBorder;
            case Constants.dark: return ThemeDark.colorBorder;
            case Constants.light: return ThemeLight.colorBorder;
            case Constants.lowVisibility: return ThemeLowVisibility.colorBorder;
        }
    }

    property color colorBg: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorBg;
            case Constants.dark: return ThemeDark.colorBg;
            case Constants.light: return ThemeLight.colorBg;
            case Constants.lowVisibility: return ThemeLowVisibility.colorBg;
        }
    }

    property color colorButtonEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonEnabled;
            case Constants.dark: return ThemeDark.colorButtonEnabled;
            case Constants.light: return ThemeLight.colorButtonEnabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorButtonEnabled;
        }
    }

    property color colorButtonDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonDisabled;
            case Constants.dark: return ThemeDark.colorButtonDisabled;
            case Constants.light: return ThemeLight.colorButtonDisabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorButtonDisabled;
        }
    }

    property color colorShadowEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorShadowEnabled;
            case Constants.dark: return ThemeDark.colorShadowEnabled;
            case Constants.light: return ThemeLight.colorShadowEnabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorShadowEnabled;
        }
    }

    property color colorShadowDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorShadowDisabled;
            case Constants.dark: return ThemeDark.colorShadowDisabled;
            case Constants.light: return ThemeLight.colorShadowDisabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorShadowDisabled;
        }
    }

    property color colorButtonTextEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonTextEnabled;
            case Constants.dark: return ThemeDark.colorButtonTextEnabled;
            case Constants.light: return ThemeLight.colorButtonTextEnabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorButtonTextEnabled;
        }
    }

    property color colorButtonTextDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorButtonTextDisabled;
            case Constants.dark: return ThemeDark.colorButtonTextDisabled;
            case Constants.light: return ThemeLight.colorButtonTextDisabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorButtonTextDisabled;
        }
    }

    property color colorPanelEnabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorPanelEnabled;
            case Constants.dark: return ThemeDark.colorPanelEnabled;
            case Constants.light: return ThemeLight.colorPanelEnabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorPanelEnabled;
        }
    }

    property color colorPanelDisabled: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorPanelDisabled;
            case Constants.dark: return ThemeDark.colorPanelDisabled;
            case Constants.light: return ThemeLight.colorPanelDisabled;
            case Constants.lowVisibility: return ThemeLowVisibility.colorPanelDisabled;
        }
    }

    property color colorFilterNotReady: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterNotReady;
            case Constants.dark: return ThemeDark.colorFilterNotReady;
            case Constants.light: return ThemeLight.colorFilterNotReady;
            case Constants.lowVisibility: return ThemeLowVisibility.colorFilterNotReady;
        }
    }

    property color colorFilterReady: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterReady;
            case Constants.dark: return ThemeDark.colorFilterReady;
            case Constants.light: return ThemeLight.colorFilterReady;
            case Constants.lowVisibility: return ThemeLowVisibility.colorFilterReady;
        }
    }

    property color colorFilterUsed: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterUsed;
            case Constants.dark: return ThemeDark.colorFilterUsed;
            case Constants.light: return ThemeLight.colorFilterUsed;
            case Constants.lowVisibility: return ThemeLowVisibility.colorFilterUsed;
        }
    }

    property color colorFilterInfected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorFilterInfected;
            case Constants.dark: return ThemeDark.colorFilterInfected;
            case Constants.light: return ThemeLight.colorFilterInfected;
            case Constants.lowVisibility: return ThemeLowVisibility.colorFilterInfected;
        }
    }

    property color colorClean: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorClean;
            case Constants.dark: return ThemeDark.colorClean;
            case Constants.light: return ThemeLight.colorClean;
            case Constants.lowVisibility: return ThemeLowVisibility.colorClean;
        }
    }

    property color colorInfected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorInfected;
            case Constants.dark: return ThemeDark.colorInfected;
            case Constants.light: return ThemeLight.colorInfected;
            case Constants.lowVisibility: return ThemeLowVisibility.colorInfected;
        }
    }

    property color colorWaiting: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorWaiting;
            case Constants.dark: return ThemeDark.colorWaiting;
            case Constants.light: return ThemeLight.colorWaiting;
            case Constants.lowVisibility: return ThemeLowVisibility.colorWaiting;
        }
    }

    property color colorRunning: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorRunning;
            case Constants.dark: return ThemeDark.colorRunning;
            case Constants.light: return ThemeLight.colorRunning;
            case Constants.lowVisibility: return ThemeLowVisibility.colorRunning;
        }
    }

    property color colorSelected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorSelected;
            case Constants.dark: return ThemeDark.colorSelected;
            case Constants.light: return ThemeLight.colorSelected;
            case Constants.lowVisibility: return ThemeLowVisibility.colorSelected;
        }
    }

    property color colorIconFolder: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorIconFolder;
            case Constants.dark: return ThemeDark.colorIconFolder;
            case Constants.light: return ThemeLight.colorIconFolder;
            case Constants.lowVisibility: return ThemeLowVisibility.colorIconFolder;
        }
    }

    property color colorIconFile: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorIconFile;
            case Constants.dark: return ThemeDark.colorIconFile;
            case Constants.light: return ThemeLight.colorIconFile;
            case Constants.lowVisibility: return ThemeLowVisibility.colorIconFile;
        }
    }

    property color colorWarning: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorWarning;
            case Constants.dark: return ThemeDark.colorWarning;
            case Constants.light: return ThemeLight.colorWarning;
            case Constants.lowVisibility: return ThemeLowVisibility.colorWarning;
        }
    }

    property color colorSuccess: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorSuccess;
            case Constants.dark: return ThemeDark.colorSuccess;
            case Constants.light: return ThemeLight.colorSuccess;
            case Constants.lowVisibility: return ThemeLowVisibility.colorSuccess;
        }
    }

    property double panelSaturation: {
        switch(root.theme) {
            case Constants.dark: return ThemeDark.panelSaturation
            case Constants.light: return ThemeLight.panelSaturation
            case Constants.lowVisibility: return ThemeLowVisibility.panelSaturation
        }
    }

    property double panelBrightness: {
        switch(root.theme) {
            case Constants.dark: return ThemeDark.panelBrightness
            case Constants.light: return ThemeLight.panelBrightness
            case Constants.lowVisibility: return ThemeLowVisibility.panelBrightness
        }
    }

    property color colorNotProtected: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorNotProtected;
            case Constants.dark: return ThemeDark.colorNotProtected;
            case Constants.light: return ThemeLight.colorNotProtected;
            case Constants.lowVisibility: return ThemeLowVisibility.colorNotProtected;
        }
    }

    property color colorRestricted: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorRestricted;
            case Constants.dark: return ThemeDark.colorRestricted;
            case Constants.light: return ThemeLight.colorRestricted;
            case Constants.lowVisibility: return ThemeLowVisibility.colorRestricted;
        }
    }

    property color colorSecret: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorSecret;
            case Constants.dark: return ThemeDark.colorSecret;
            case Constants.light: return ThemeLight.colorSecret;
            case Constants.lowVisibility: return ThemeLowVisibility.colorSecret;
        }
    }

    property color colorTopSecret: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.colorTopSecret;
            case Constants.dark: return ThemeDark.colorTopSecret;
            case Constants.light: return ThemeLight.colorTopSecret;
            case Constants.lowVisibility: return ThemeLowVisibility.colorTopSecret;
        }
    }
    
    property double logoBrightness: {
        switch(root.theme) {
            case Constants.wireframe : return ThemeWireframe.logoBrightness;
            case Constants.dark: return ThemeDark.logoBrightness;
            case Constants.light: return ThemeLight.logoBrightness;
            case Constants.lowVisibility: return ThemeLowVisibility.logoBrightness;
        }
    }


  
}
