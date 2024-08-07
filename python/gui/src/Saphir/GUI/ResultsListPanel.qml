import QtQuick
import QtQuick.Controls
import net.alefbet

ResultsListPanelUi {
    id: root

    pnlDigits.infected: ApplicationController.infected
    pnlDigits.clean: ApplicationController.clean
}
