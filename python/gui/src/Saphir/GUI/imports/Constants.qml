pragma Singleton
import QtQuick
import net.alefbet

QtObject {
    //Enumérations
    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
    //Modes de couleurs disponibles
    enum ColorMode {
        LIGHT = 0,
        DARK = 1,
        STEALTH = 2
    }
    //Etats possibles d'un fichier
    enum FileState {
        NOT_ANALYSED = 0,
        ANALYSING = 1,
        SANE = 2,
        INFECTED = 3
    }
    //Etats possibles d'un antivirus
    enum AntivirusState {
        STARTING = 0,
        RUNNING = 1,
        ERROR = 2
    }

    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

    //Propriétés de l'application
    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
        // -- Format de l'application
    property int width: 1280
    property int height: 800

        // -- Propriétés d'avancement de l'analyse
    property real globalProgress: ApplicationController.globalProgress / 100.0
    property int globalTimeLeft: ApplicationController.remainingTime
    property int countNotAnalysedFiles: 0
    property int countAnalysingFiles: 0
    property int countSaneFiles: 0
    property int countInfectedFiles: 0
    property bool isCopyingSaneFiles: ApplicationController.transferProgress > 0
    property real copyProgress: 0.0

        // -- Propriétés état du système
    property int diskState: 0
    property int currentDirectoryId: 0
    property string currentDirectory: "/"
    property bool isAnalysePlaying: ApplicationController.systemState === Enums.SystemState.SystemAnalysisRunning
    property real batteryLevel: 1.0
    property bool isInputUSBPlugged: ApplicationController.sourceReady
    property string inputUSBName: ApplicationController.sourceName
    property bool isOutputUSBPlugged: ApplicationController.targetReady
    property string outputUSBName: ApplicationController.targetName
    property bool isFileSelectionMode: ApplicationController.analysisMode === Enums.AnalysisMode.AnalyseSelection
    property bool isWired: false
    property bool afficherAide: false

        // -- Propriétés de couleurs de l'application
    property int currentDisplayMode: 0
    property int currentColorMode: Constants.DARK
    property string colorModePath: Qt.resolvedUrl("../images/dark_mode/") +"Sombre_"
    property string colorModePrefix: "Sombre_"
    property string colorText: "#FFFFFF"
    property color colorRed: "#B0283A"
    property string colorGreen: "#8BC34A"
    property string colorBlue: "#87CEEB"
    property color colorSystemUsed: "#B0283A"

        // -- Modèles de données
    //Modèle de données de parcours de fichiers
    //Exemples
    //1 : ListElement{type:"folder";name:"racine";selected:false;status:Constants.FileState.NOT_ANALYSED;parent: -1}
    //2 : ListElement{type:"folder";name:"main";selected:false;status:Constants.FileState.NOT_ANALYSED;parent: 0}
    //Le champ parent correspond à l'index dans la liste du dossier parent
    property var fileList: ApplicationController.inputFilesListProxyModel
    /*:ListModel
    {
        //Le dossier racine est important pour y mettre les fichiers à la racine
        ListElement{backId:0;type:"folder";name:"racine";selected:false;status:Constants.FileState.NOT_ANALYSED;parent: -1}
        ListElement{backId:5;type:"file";name:"4";selected:false;status:Constants.FileState.INFECTED;parent: 0}
        ListElement{backId:1;type:"folder";name:"child";selected:false;status:Constants.FileState.NOT_ANALYSED;parent: 0}
        ListElement{backId:2;type:"file";name:"1";selected:false;status:Constants.FileState.NOT_ANALYSED;parent: 1}
        ListElement{backId:3;type:"file";name:"fichierDeTest";selected:false;status:Constants.FileState.ANALYSING;parent: 1}
        ListElement{backId:4;type:"file";name:"3";selected:false;status:Constants.FileState.ANALYSING;parent: 1}
        ListElement{backId:6;type:"file";name:"5";selected:false;status:Constants.FileState.SANE;parent: 1}
    }*/
    //Modèle dee données des fichiers envoyés à l'analyse
    //Exemple : ListElement{type:"file";name:"test";selected:false;status:Constants.FileState.ANALYSING;progress: 0.00;backId: 7}
    //property var runningFileList: ApplicationController.queueListModel
    /*: ListModel
    {
        ListElement{type:"file";name:"test";selected:false;status:Constants.FileState.ANALYSING;progress:0.00;backId: 7}
        ListElement{type:"file";name:"test2";selected:false;status:Constants.FileState.ANALYSING;progress:0.00;backId: 8}
    }*/
    //Modèle de données des antivirus
    property ListModel antivirusList:ListModel
    {
        ListElement{backId:0;name:"Avast";   state:Constants.AntivirusState.STARTING}
        ListElement{backId:1;name:"Kapersky";state:Constants.AntivirusState.RUNNING}
        ListElement{backId:2;name:"CLAMAV";  state:Constants.AntivirusState.ERROR}
        ListElement{backId:3;name:"CLAMAV2"; state:18}
    }
    //Modèle de données des logs
    //Exemple : ListElement{log:"Hello World!"}
    property ListModel logsList :ListModel
    {
        ListElement{log:"Hello World!"}
        ListElement{log:"Hello World 1!"}
        ListElement{log:"Hello World 2!"}
        ListElement{log:"Hello World 3!"}
    }

    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

    //Signaux de l'application
    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

        // -- Signaux à émettre
    //Signal de rechargement de l'application au clic d'un mode de couleur (propre au front)
    signal reloadRequested()
    //Signal permettant de mettre à jour l'avancement de l'analyse
    signal updateProgress(real newProgress, real newTimeLeft)
    //Signal permettant de mettre à jour le nombre de fichiers non analysés, en cours d'analyse, sains et infectés
    signal updateStateTracker()
    //Signal indiquant le changement de dossier
    signal updateCurrentPath(int idFolder, string newPath)
    //Signal mettant à jour les progrès de l'analyse sur un fichier particulier
    signal updateFileProgress(int backId, real newProgress)
    //Signal mettant à jour le statut d'un fichier analysé
    signal updateFileStatus(int backId, int newStatus)
    //Signal mettant à jour le niveau de batterie
    signal updateBatteryLevel(real newBatteryLevel)
    //Signal vidant la liste des fichiers lus
    signal clearFileList()
    //Signal vidant la liste des fichiers analysés
    signal clearRunningFileList()
    //Signal mettant à jour le progrès de la copie des fichiers sains
    signal updateCopySaneFilesProgress(real newProgress)
    //Signal indiquant la clé USB d'entrée branchée
    signal inputUSBPlugged(string usbName)
    //Signal indiquant que la clé USB d'entrée est débranchée
    signal inputUSBUnplugged()
    //Signal indiquant la clé USB de sortie branchée
    signal outputSUBPlugged(string usbName)
    //Signal indiquant que la clé USB de sortie est débranchée
    signal outputUSBUnplugged()
    //Signal ajoutant un log à la liste des logs
    signal addLog(string newLog)
    //Signal demandant de vider la liste des logs
    signal clearLogs()
    //Signal ajoutant un antivirus à la liste des antivirus
    signal addAntivirus(int newId, string newName, int newState)
    //Signal mettant à jour l'état d'un antivirus
    signal updateAntivirusSate(int aBackId, int newState)
    //Signal pour nettoyer la liste des antivirus
    signal clearAntivirusList()
    //Signal modifiant l'état courant du disque
    signal updateDiskState(int newState)
    //Signal indiquant le mode d'affichage sélectionné
    signal changeDisplayMode(int newMode)
    //Signal demandant au splashscreen de ne plus s'afficher
    signal hideSplashScreen()
    //Signal indiquant si l'appareil est branché ou non
    signal deviceWired(bool isDeviceWired)
    //Signal modifiant le texte affiché sur le splashscreen
    signal updateSplashScreenText(string newText)

        // -- Signaux sur lesquels se connecter
    //Signal demandant la copie des fichiers sains analysés
    signal copySaneFilesRequested()
    //Signal demandant l'ouverture d'un dossier
    signal enterFolder(int idFolder)
    //Signal ajoutant un fichier à la liste des fichiers devant être analysés
    signal analyseFile(string type, string name, bool selected, int status, real analyseProgress, int backId)
    //Signal notifiant l'appui du bouton pause
    signal pause()
    //Signal notifiant l'appui du bouton play
    signal play()
    //Signal demandant la remise à zéro de l'application
    signal restart()
    //Signal demandant la fermeture de l'application
    signal quit()
    //Signal demandant la copie des fichiers sains
    signal copySaneFiles()


    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

    //Fonctions
    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~
    //Méthode permettant de changer de mode de couleur de l'application
    function updateColorMode(mode)
    {
        if(mode === Constants.currentColorMode)
            return

        console.log("Mode détecté : ", mode)
        switch (mode)
        {
        case Constants.ColorMode.STEALTH:
            Constants.colorModePath = Qt.resolvedUrl("../images/stealth_mode/") +"Furtif_"
            Constants.colorModePrefix = "Furtif_"            
            Constants.currentColorMode = Constants.ColorMode.STEALTH
            Constants.colorRed = "#2F0A35"
            Constants.colorGreen = "#0B0F14"
            Constants.colorBlue = "#171717"
            Constants.colorText = /*"#1E1E1E"*/"#3B3B3B"
            Constants.colorSystemUsed = "#2F0A35"            
            break;
        case Constants.ColorMode.DARK:
            Constants.colorModePath = Qt.resolvedUrl("../images/dark_mode/") +"Sombre_"
            Constants.colorModePrefix = "Sombre_"
            Constants.currentColorMode = Constants.ColorMode.DARK
            Constants.colorRed = "#B0283A"
            Constants.colorGreen = "#8BC34A"
            Constants.colorBlue = "#87CEEB"
            Constants.colorText = "#FFFFFF"
            Constants.colorSystemUsed = "#926c6d"
            break;
        default:
            Constants.colorModePath = Qt.resolvedUrl("../images/light_mode/") +"Clair_"
            Constants.colorModePrefix = "Clair_"
            Constants.currentColorMode = Constants.ColorMode.LIGHT
            Constants.colorRed = "#B0283A"
            Constants.colorGreen = "#32CD32"
            Constants.colorBlue = "#087BF8"
            Constants.colorText = "#525051"
            Constants.colorSystemUsed = "#B0283A"
            break;
        }
        Constants.reloadRequested()
    }
    //Méthode permettant d'ajouter un nouvel élément à la liste des fichiers en cours d'analyse
    function addToAnalyse(/*string*/ type,
                          /*string*/ filanem,
                          /*bool*/ selected,
                          /*int*/ status,
                          /*real*/ progress,
                          /*int*/ filepath)
    {
        console.debug("addToAnalyse")
        ApplicationController.enqueue_file(type, filepath)
        
    }
    //Méthode permettant d'ajouter un nouvel élément à la liste des fichiers en cours d'analyse
    function removeFromAnalyse(/*string*/ type,
                          /*string*/ filename,
                          /*bool*/ selected,
                          /*int*/ status,
                          /*real*/ progress,
                          /*int*/ filepath)
    {
        ApplicationController.dequeue_file(filepath)
        
    }
    //Méthode vérifiant si un fichier n'est pas déjà dans la phase d'analyse
    function isInRunningFileList(searchId)
    {
        for (let i = 0; i < Constants.runningFileList.count; i++)
        {
            if(Constants.runningFileList.get(i).backId === searchId)
            {
                return true
            }
        }
        return false
    }
    //Méthode ajoutant un ensemble d'objets dans la liste de sélection
    /*function addToSelection(data)
    {
        for (let file of data) {
            Constants.runningFileList.append({   backId: file.id,
                                                 name: file.name,
                                                 type: file.type,
                                                 status: file.status,
                                                 selected: file.selected,
                                                 parent: file.parent})
        }
    }*/

    //=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~

}
