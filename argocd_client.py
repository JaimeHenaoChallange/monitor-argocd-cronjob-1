import requests
import urllib3
from config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ArgoCDClient:
    @staticmethod
    def get_applications(timeout=10):
        headers = {"Authorization": "Bearer ***"}
        print(f"🔍 Enviando solicitud a {Config.ARGOCD_API}/applications con headers {headers}")  # Depuración
        try:
            response = requests.get(f"{Config.ARGOCD_API}/applications", headers=headers, verify=False, timeout=timeout)
            print(f"🔍 Respuesta del servidor: {response.status_code}")  # Depuración
            response.raise_for_status()
            return response.json().get("items", [])
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"❌ Connection error: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"❌ Timeout error: {timeout_err}")
        except Exception as e:
            print(f"❌ Error desconocido: {e}")
        return []

    @staticmethod
    def sync_app(app_name, timeout=10):
        headers = {"Authorization": "Bearer ***", "Content-Type": "application/json"}
        print(f"🔍 Enviando solicitud de sincronización para la aplicación {app_name}")  # Depuración
        try:
            response = requests.post(f"{Config.ARGOCD_API}/applications/{app_name}/sync", headers=headers, verify=False, json={}, timeout=timeout)
            print(f"🔍 Respuesta del servidor: {response.status_code}")  # Depuración
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"❌ Connection error: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"❌ Timeout error: {timeout_err}")
        except Exception as e:
            print(f"❌ Error desconocido: {e}")

    @staticmethod
    def refresh_app(app_name, timeout=10):
        headers = {"Authorization": "Bearer ***"}
        print(f"🔍 Enviando solicitud de actualización para la aplicación {app_name}")  # Depuración
        try:
            response = requests.get(f"{Config.ARGOCD_API}/applications/{app_name}?refresh=true", headers=headers, verify=False, timeout=timeout)
            print(f"🔍 Respuesta del servidor: {response.status_code}")  # Depuración
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"❌ Connection error: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"❌ Timeout error: {timeout_err}")
        except Exception as e:
            print(f"❌ Error desconocido: {e}")

    @staticmethod
    def get_application_status(app_name, timeout=10):
        headers = {"Authorization": "Bearer ***"}
        print(f"🔍 Enviando solicitud para obtener el estado de la aplicación {app_name}")  # Depuración
        try:
            response = requests.get(f"{Config.ARGOCD_API}/applications/{app_name}", headers=headers, verify=False, timeout=timeout)
            print(f"🔍 Respuesta del servidor: {response.status_code}")  # Depuración
            response.raise_for_status()
            app_info = response.json()
            health_status = app_info.get("status", {}).get("health", {}).get("status", "Unknown")
            sync_status = app_info.get("status", {}).get("sync", {}).get("status", "Unknown")
            print(f"🔍 Estado de salud: {health_status}, Estado de sincronización: {sync_status}")  # Depuración
            return health_status, sync_status
        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"❌ Connection error: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"❌ Timeout error: {timeout_err}")
        except Exception as e:
            print(f"❌ Error desconocido: {e}")
        return "Unknown", "Unknown"
