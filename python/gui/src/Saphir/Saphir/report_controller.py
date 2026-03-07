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
        return "Scan report.pdf"

    def get_report_filepath(self):
        out_dir = tempfile.gettempdir()
        out_path = os.path.join(out_dir, self.get_report_filename())
        return out_path

    def make_report(
            self,
            files:dict,
            clean_files_count:int,
            infected_files_count:int,
            analyzed_files_count:int,
            copied_files_count:int,
            start_datetime:datetime,
            end_datetime:datetime,
            equipement_id:str,
            storage_name:str,
            safecor_version:str,
            saphir_version:str,
            antiviruses:dict
        ):

        analysis_details = []
        for fichier in files.values():
            analysis_details.append({
                "filepath": fichier.get("filepath", "inconnu"),
                "fingerprint": fichier.get("fingerprint", "inconnu"),
                "results": fichier.get("results", {})
            })

        data = {
            "analysis_result": "succes" if infected_files_count == 0 else "erreur",
            "label_scan_result": "No threat has been detected." if infected_files_count == 0 else "Threats have been idenfitied.",
            "start_datetime": start_datetime.strftime("%d/%m/%Y %H:%M:%S"),
            "end_datetime": end_datetime.strftime("%d/%m/%Y %H:%M:%S"),
            "equipement_id": equipement_id,
            "storage_name": storage_name,
            "partitions": "",
            "analyzed_files_count": analyzed_files_count,
            "clean_files_count": clean_files_count,
            "infected_files_count": infected_files_count,
            "copied_files_count": copied_files_count,
            "safecor_version": safecor_version,
            "saphir_version": saphir_version,
            "antiviruses": antiviruses,            
            "analysis_details": analysis_details
        }

        script_dir = os.path.dirname(os.path.realpath(__file__))
        templates_dir = os.path.join(script_dir, 'templates')
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template('scan_report_en.html')

        html_content = template.render(data)

        out_filepath = self.get_report_filepath()
        HTML(string=html_content, base_url=templates_dir).write_pdf(out_filepath)
        
        print("Scan report generated in the file", out_filepath)
        self.reportGenerated.emit()