import sys
import os
import time
import subprocess
from logic.argocd_client import ArgoCDClient
from logic.slack_notifier import SlackNotifier

# Agregar el directorio de lógica al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logic"))

REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos
GIT_REPO_PATH = "/tmp/argocd-repo"  # Ruta temporal para clonar el repositorio
GIT_REPO_URL = "https://github.com/JaimeHenaoChallange/monitor-argocd-cronjob-1.git"  # URL del repositorio
GIT_BRANCH = "main"  # Rama principal

# Diccionario para rastrear el estado, intentos y versión de las aplicaciones
app_states = {}

def rollback_application(app_name):
    """Realiza un rollback de la aplicación."""
    try:
        # Lógica de rollback (similar a lo implementado anteriormente)
        print(f"🔄 Rollback completado para '{app_name}'.")
        SlackNotifier.send_notification(
            app_name, "Rollback", 0, f"Rollback completado para la aplicación '{app_name}'.", level="critical"
        )
    except Exception as e:
        print(f"❌ Error al realizar el rollback para '{app_name}': {e}")
        SlackNotifier.send_notification(
            app_name, "Rollback", 0, f"El rollback para la aplicación '{app_name}' falló. Requiere intervención manual.", level="critical"
        )

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

                # Excluir la aplicación 'argocd-monitor' del análisis
                if app_name == "argocd-monitor":
                    print(f"⏩ Excluyendo la aplicación '{app_name}' del análisis.")
                    continue

                print(f"🔄 Procesando la aplicación: {app_name}")  # Mensaje de depuración
                ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

                # Inicializar estado si no está registrado
                if app_name not in app_states:
                    app_states[app_name] = {
                        "health_status": health_status,
                        "sync_status": sync_status,
                        "version": current_version,
                        "attempts": 0,
                        "paused": False,
                        "notified_recovery": False,
                        "notified_rollback": False,
                    }

                state = app_states[app_name]

                # Si la aplicación está en pausa, verificar si necesita rollback
                if state["paused"]:
                    if health_status in ["Degraded", "Error"] and current_version != state["version"]:
                        if not state["notified_rollback"]:
                            SlackNotifier.send_notification(
                                app_name, "Rollback", 0, f"Iniciando rollback para la versión {current_version}.", level="critical"
                            )
                            state["notified_rollback"] = True
                        rollback_application(app_name)
                        state["paused"] = False
                    continue

                # Manejar estado OutOfSync
                if sync_status == "OutOfSync":
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

                # Manejar estado Degraded o Error
                elif health_status in ["Degraded", "Error"]:
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

                # Notificar si la aplicación vuelve a estar Healthy
                if health_status == "Healthy" and not state["notified_recovery"]:
                    print(f"✅ '{app_name}' ha vuelto al estado Healthy.")
                    SlackNotifier.send_notification(
                        app_name, "Healthy", 0, "La aplicación ha vuelto al estado Healthy.", level="info"
                    )
                    state["notified_recovery"] = True

                # Actualizar estado y versión
                state["health_status"] = health_status
                state["sync_status"] = sync_status
                state["version"] = current_version

            time.sleep(60)

        except Exception as e:
            print(f"❌ Error en el ciclo principal: {e}")
            import traceback
            traceback.print_exc()  # Agregar traza para depuración
            time.sleep(30)

if __name__ == "__main__":
    main()
