from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, QPersistentModelIndex, Property, Signal
from QueueListModel import QueueListModel
from Enums import Roles, FileStatus

class QueueListProxyModel(QSortFilterProxyModel):    

    filtreSainsChanged = Signal()
    filtreInfectesChanged = Signal()
    filtreAutresChanged = Signal()


    def __init__(self, source_model:QueueListModel, parent=None):
        super().__init__(parent)   
        self.setSourceModel(source_model)        


    def filterAcceptsRow(self, source_row:int, source_parent:QModelIndex|QPersistentModelIndex):
        return True       
    

    def lessThan(self, source_left: QModelIndex | QPersistentModelIndex, source_right: QModelIndex | QPersistentModelIndex) -> bool:      
        return True  
        leftStatus = self.sourceModel().data(source_left, Roles.RoleStatus)
        rightStatus = self.sourceModel().data(source_right, Roles.RoleStatus)
        
        # On affiche dans l'ordre les fichiers infectés, puis les fichiers en cours d'analyse le reste
        if leftStatus == FileStatus.FileInfected.value or leftStatus == FileStatus.FileAnalysisError.value:
            return True
        elif rightStatus == FileStatus.FileInfected.value or leftStatus == FileStatus.FileAnalysisError.value:
            return False
        elif leftStatus == FileStatus.FileClean.value:
            return False 
        elif rightStatus == FileStatus.FileClean.value:
            return True 
        
        return False
    

    def on_data_changed(self):
        pass
        #self.__set_regle_filtrage_auto()

        #if self.sourceModel().rowCount() < self.__max_rows:
            # Si la quantité d'enregistrement est inférieur au maximum
            # on trie les lignes
        #    self.sort(0)    


    ## Getters et setters
    def __get_filtre_sains(self):
        return self.sourceModel().get_filtre_sains()
        #return self.__filtreSains


    def __set_filtre_sains(self, filtre:bool):
        self.sourceModel().set_filtre_sains(filtre)
        #self.__filtreSains = filtre
        self.filtreSainsChanged.emit()
        #self.invalidateFilter()


    def __get_filtre_infectes(self):
        return self.sourceModel().get_filtre_infectes()
        #return self.__filtreInfectes


    def __set_filtre_infectes(self, filtre:bool):
        self.sourceModel().set_filtre_infectes(filtre)
        #self.__filtreInfectes = filtre
        self.filtreInfectesChanged.emit()
        #self.invalidateFilter()


    def __get_filtre_autres(self):
        return self.sourceModel().get_filtre_autres()
        #return self.__filtreAutres


    def __set_filtre_autres(self, filtre:bool):
        self.sourceModel().set_filtre_autres(filtre)
        #self.__filtreAutres = filtre
        self.filtreAutresChanged.emit()
        #self.invalidateFilter()


    filterClean = Property(bool, __get_filtre_sains, __set_filtre_sains, notify=filtreSainsChanged)
    filterInfected = Property(bool, __get_filtre_infectes, __set_filtre_infectes, notify=filtreInfectesChanged)
    filterOther = Property(bool, __get_filtre_autres, __set_filtre_autres, notify=filtreAutresChanged)