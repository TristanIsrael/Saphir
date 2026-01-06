
// Created with Qt Design Studio (version 4.8.1), Mon Jan 5 14:51:40 2026
// Do not manually edit this file, it will be overwritten if effect is modified in Qt Design Studio.

import QtQuick
import QtQuick.Layouts
import HelperWidgets
import StudioTheme as StudioTheme

Column {

    Section {
        caption: "General"
        width: parent.width

        SectionLayout {
            PropertyLabel {
                text: "Extra Margin"
                tooltip: "This property specifies how much of extra space is reserved for the effect outside the parent geometry."
            }

            SecondColumnLayout {
                SpinBox {
                    minimumValue: 0
                    maximumValue: 1000
                    decimals: 0
                    stepSize: 1
                    sliderIndicatorVisible: true
                    backendValue: backendValues.extraMargin
                    implicitWidth: StudioTheme.Values.singleControlColumnWidth
                                   + StudioTheme.Values.actionIndicatorWidth
                }
                ExpandingSpacer {}
            }
        }
    }

    Section {
        caption: "Blur Helper"
        width: parent.width

        SectionLayout {

            PropertyLabel {
                text: "Multiplier"
                tooltip: "This property defines a multiplier for extending the blur radius.\n\nBy default, the property is set to 0.0 (not multiplied). Incresing the multiplier extends the blur radius, but decreases the blur quality. This is more performant option for a bigger blur radius than Max Blur Level as it doesn't increase the amount of texture lookups.\n\nNote: This affects to both blur and shadow effects."
            }

            SecondColumnLayout {

                SpinBox {
                    minimumValue: 0
                    maximumValue: 2
                    decimals: 2
                    stepSize: .01
                    sliderIndicatorVisible: true
                    backendValue: backendValues.blurMultiplier
                    implicitWidth: StudioTheme.Values.singleControlColumnWidth
                                   + StudioTheme.Values.actionIndicatorWidth
                }

                ExpandingSpacer {}
            }
        }
    }

    Section {
        caption: "Fast Blur"
        width: parent.width

        SectionLayout {

            PropertyLabel {
                text: "Amount"
                tooltip: "Sets the amount of blur."
            }

            SecondColumnLayout {

                SpinBox {
                    minimumValue: 0
                    maximumValue: 1
                    decimals: 2
                    stepSize: .01
                    sliderIndicatorVisible: true
                    backendValue: backendValues.fastBlurAmount
                    implicitWidth: StudioTheme.Values.singleControlColumnWidth
                                   + StudioTheme.Values.actionIndicatorWidth
                }

                ExpandingSpacer {}
            }
        }
    }
}
