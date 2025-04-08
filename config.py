import os

class Config:
    ARGOCD_API = os.getenv("ARGOCD_API", "https://argocd-server.argocd.svc.cluster.local/api/v1")
    ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GIT_REPO_URL = os.getenv("GIT_REPO_URL", "https://github.com/JaimeHenaoChallange/monitor-argocd-cronjob-1.git")
    GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))

    @staticmethod
    def validate():
        required_vars = ["ARGOCD_API", "ARGOCD_TOKEN", "SLACK_WEBHOOK_URL", "GITHUB_TOKEN"]
        for var in required_vars:
            if not getattr(Config, var):
                raise ValueError(f"❌ Faltan variables de entorno requeridas: {var}")
