import requests
from config import Config

class SlackNotifier:
    @staticmethod
    def send_notification(app_name, status, attempts, action="", level="info"):
        """Envía una notificación a Slack con diferentes niveles de prioridad."""
        color = "#36a64f" if level == "info" else "#ff0000"  # Verde para info, rojo para alertas
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Estado de la aplicación: {app_name}",
                    "fields": [
                        {"title": "Estado", "value": status, "short": True},
                        {"title": "Intentos", "value": str(attempts), "short": True},
                        {"title": "Acción", "value": action, "short": False},
                    ],
                }
            ]
        }
        try:
            print(f"🔍 Enviando notificación a Slack para la aplicación '{app_name}'")  # Depuración
            response = requests.post(Config.SLACK_WEBHOOK_URL, json=message)
            response.raise_for_status()
            print(f"✅ Notificación enviada a Slack para la aplicación '{app_name}'.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al enviar notificación a Slack: {e}")