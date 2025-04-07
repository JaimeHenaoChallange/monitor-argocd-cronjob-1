import os
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

class Config:
    ARGOCD_API = os.getenv("ARGOCD_API", "http://argocd-monitor-service.poc.svc.cluster.local/api/v1")
    ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    @staticmethod
    def validate():
        if not Config.ARGOCD_API or not Config.ARGOCD_TOKEN or not Config.SLACK_WEBHOOK_URL:
            raise ValueError("❌ Faltan variables de entorno requeridas: ARGOCD_API, ARGOCD_TOKEN o SLACK_WEBHOOK_URL.")
