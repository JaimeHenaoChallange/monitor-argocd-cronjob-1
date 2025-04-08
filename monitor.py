import sys
import os
import time
import subprocess
import requests
from logic.argocd_client import ArgoCDClient
from logic.slack_notifier import SlackNotifier
from config import Config

# Validar configuraciones al inicio
Config.validate()

# Agregar el directorio de lógica al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logic"))

# Usar las configuraciones centralizadas
REQUEST_TIMEOUT = Config.REQUEST_TIMEOUT
GIT_REPO_URL = Config.GIT_REPO_URL
GIT_BRANCH = Config.GIT_BRANCH
GITHUB_API_URL = "https://api.github.com/repos/JaimeHenaoChallange/monitor-argocd-cronjob-1/dispatches"
GITHUB_TOKEN = Config.GITHUB_TOKEN

# Diccionario para rastrear el estado, intentos y versión de las aplicaciones
app_states = {}

def trigger_rollback(app_name, commit_hash):
    """Dispara el workflow de rollback en GitHub Actions."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "event_type": "trigger-rollback",
        "client_payload": {
            "app_name": app_name,
            "commit_hash": commit_hash,
        },
    }
    response = requests.post(GITHUB_API_URL, headers=headers, json=data)
    if response.status_code == 204:
        print(f"✅ Workflow de rollback disparado para la aplicación '{app_name}'.")
        SlackNotifier.send_notification(
            app_name, "Rollback", 0, f"Workflow de rollback disparado para la aplicación '{app_name}'.", level="critical"
        )
    else:
        print(f"❌ Error al disparar el workflow: {response.status_code}, {response.text}")
        SlackNotifier.send_notification(
            app_name, "Rollback", 0, f"Error al disparar el workflow de rollback para '{app_name}'.", level="critical"
        )

def handle_out_of_sync(app_name, state):
    """Maneja el estado OutOfSync."""
    if state["attempts"] < 3:
        if state["attempts"] == 0:
            SlackNotifier.send_notification(
                app_name, "OutOfSync", 0, "Intentando recuperación (3 intentos programados).", level="alert"
            )
        print(f"🔄 '{app_name}' está OutOfSync. Intentando sincronizar (Intento {state['attempts'] + 1}/3)...")
        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
        state["attempts"] += 1
    else:
        print(f"⏸️ '{app_name}' no se pudo sincronizar después de 3 intentos. Pausando...")
        SlackNotifier.send_notification(
            app_name, "OutOfSync", state["attempts"], "La aplicación fue pausada después de 3 intentos fallidos.", level="critical"
        )
        state["paused"] = True

def handle_degraded_or_error(app_name, health_status, state):
    """Maneja los estados Degraded o Error."""
    if state["attempts"] < 3:
        if state["attempts"] == 0:
            SlackNotifier.send_notification(
                app_name, health_status, 0, "Intentando recuperación (3 intentos programados).", level="alert"
            )
        print(f"🔄 '{app_name}' está en estado {health_status}. Intentando recuperar (Intento {state['attempts'] + 1}/3)...")
        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
        state["attempts"] += 1
    else:
        print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Pausando...")
        SlackNotifier.send_notification(
            app_name, health_status, state["attempts"], "La aplicación fue pausada después de 3 intentos fallidos.", level="critical"
        )
        state["paused"] = True

def process_application(app, state):
    """Procesa una aplicación individual."""
    app_name = app.get("metadata", {}).get("name", "Desconocido")
    health_status = app["status"]["health"]["status"]
    sync_status = app["status"]["sync"]["status"]
    current_version = app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")

    # Excluir la aplicación 'argocd-monitor' del análisis
    if app_name == "argocd-monitor":
        print(f"⏩ Excluyendo la aplicación '{app_name}' del análisis.")
        return

    print(f"🔄 Procesando la aplicación: {app_name}")
    ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

    # Si la aplicación está en pausa, verificar si necesita rollback
    if state["paused"]:
        if health_status in ["Degraded", "Error"] and current_version != state["version"]:
            if not state["notified_rollback"]:
                trigger_rollback(app_name, current_version)
                state["notified_rollback"] = True
            state["paused"] = False
        return

    # Manejar estado OutOfSync
    if sync_status == "OutOfSync":
        handle_out_of_sync(app_name, state)
    elif health_status in ["Degraded", "Error"]:
        handle_degraded_or_error(app_name, health_status, state)

    # Actualizar estado y versión
    state["health_status"] = health_status
    state["sync_status"] = sync_status
    state["version"] = current_version

def main():
    global app_states
    print("🔧 Iniciando el monitor de ArgoCD...")  # Mensaje de depuración
    print(f"ARGOCD_API: {os.getenv('ARGOCD_API', '***')}")
    print(f"SLACK_WEBHOOK_URL: {'***' if os.getenv('SLACK_WEBHOOK_URL') else 'No configurado'}")
    print(f"ARGOCD_TOKEN: {'***' if os.getenv('ARGOCD_TOKEN') else 'No configurado'}")

    while True:
        try:
            print("🔍 Obteniendo aplicaciones de ArgoCD...")
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

            if not apps:
                print("⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.")
                time.sleep(30)
                continue

            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")
                health_status = app["status"]["health"]["status"]
                sync_status = app["status"]["sync"]["status"]
                current_version = app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")

                # Inicializar estado si no está registrado
                if app_name not in app_states:
                    app_states[app_name] = {
                        "health_status": health_status,
                        "sync_status": sync_status,
                        "version": current_version,
                        "attempts": 0,
                        "paused": False,
                        "notified_rollback": False,
                    }

                state = app_states[app_name]
                process_application(app, state)

            time.sleep(60)

        except Exception as e:
            print(f"❌ Error en el ciclo principal: {e}")
            import traceback
            traceback.print_exc()  # Agregar traza para depuración
            time.sleep(30)

if __name__ == "__main__":
    main()
