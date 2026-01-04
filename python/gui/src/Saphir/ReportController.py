from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from datetime import datetime
from PySide6.QtCore import QObject, Signal
import os
import tempfile

class ReportController(QObject):

    reportGenerated = Signal()

    def __init__(self, parent:QObject | None = None):
        super().__init__(parent)

    def get_report_filename(self):
        return "Rapport d'inocuité.pdf"

    def get_report_filepath(self):
        out_dir = tempfile.gettempdir()
        out_path = os.path.join(out_dir, self.get_report_filename())
        return out_path

    def make_report(
            self,
            fichiers:dict,
            clean_files_count:int, 
            infected_files_count:int, 
            analyzed_files_count:int, 
            copied_files_count:int,
            date_heure_debut_analyse:datetime,
            date_heure_fin_analyse:datetime,
            identifiant_equipement:str,
            nom_support:str,
            psec_version:str,
            saphir_version:str,
            antiviruses:dict
        ):

        details_analyse = []
        for fichier in fichiers.values():
            details_analyse.append({
                "filepath": fichier.get("filepath", "inconnu"),
                "fingerprint": fichier.get("fingerprint", "inconnu"),
                "results": fichier.get("results", dict())
            })

        data = {
            "resultat_analyse": "succes" if infected_files_count == 0 else "erreur",
            "resultat_analyse_libelle": "Aucun fichier infecté n'a été identifié." if infected_files_count == 0 else "Des infections ont été identifiées.",
            "date_heure_debut_analyse": date_heure_debut_analyse.strftime("%d/%m/%Y %H:%M:%S"),
            "date_heure_fin_analyse": date_heure_fin_analyse.strftime("%d/%m/%Y %H:%M:%S"),
            "identifiant_equipement": identifiant_equipement,
            "nom_support": nom_support,
            "partitions": "",
            "nb_fichiers_analyses": analyzed_files_count,
            "nb_fichiers_sains": clean_files_count,
            "nb_fichiers_infectes": infected_files_count,
            "nb_fichiers_copies": copied_files_count,
            "psec_version": psec_version,
            "saphir_version": saphir_version,
            "antiviruses": antiviruses,            
            "details_analyse": details_analyse
        }

        script_dir = os.path.dirname(os.path.realpath(__file__))
        templates_dir = os.path.join(script_dir, 'misc/templates')
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template('rapport_innocuite.html')

        html_content = template.render(data)

        out_filepath = self.get_report_filepath()
        HTML(string=html_content, base_url=templates_dir).write_pdf(out_filepath)
        
        print("Rapport généré dans le fichier", out_filepath)
        self.reportGenerated.emit()