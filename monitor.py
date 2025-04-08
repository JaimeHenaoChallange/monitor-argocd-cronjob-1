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

# Diccionario para rastrear el estado y la versión de las aplicaciones
app_versions = {}

def get_app_version(app):
    """Obtiene la versión de la aplicación desde su etiqueta o anotación."""
    return app.get("metadata", {}).get("annotations", {}).get("argocd.argoproj.io/revision", "unknown")

def rollback_application(app_name):
    """Realiza un rollback de la aplicación actualizando el repositorio de Git."""
    try:
        # Clonar el repositorio si no está clonado
        if not os.path.exists(GIT_REPO_PATH):
            subprocess.run(["git", "clone", GIT_REPO_URL, GIT_REPO_PATH], check=True)

        # Cambiar al directorio del repositorio
        os.chdir(GIT_REPO_PATH)

        # Cambiar a la rama principal
        subprocess.run(["git", "checkout", GIT_BRANCH], check=True)

        # Revertir los últimos cambios
        subprocess.run(["git", "revert", "--no-commit", "HEAD"], check=True)

        # Confirmar y hacer push de los cambios
        subprocess.run(["git", "commit", "-m", f"Rollback for application {app_name}"], check=True)
        subprocess.run(["git", "push", "origin", GIT_BRANCH], check=True)

        # Sincronizar la aplicación en ArgoCD
        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
        print(f"✅ Rollback completado para la aplicación '{app_name}'.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al realizar el rollback para '{app_name}': {e}")

def main():
    global app_versions
    print("🔧 Iniciando el monitor de ArgoCD...")  # Mensaje de depuración
    print(f"ARGOCD_API: {os.getenv('ARGOCD_API', '***')}")
    print(f"SLACK_WEBHOOK_URL: {'***' if os.getenv('SLACK_WEBHOOK_URL') else 'No configurado'}")
    print(f"ARGOCD_TOKEN: {'***' if os.getenv('ARGOCD_TOKEN') else 'No configurado'}")

    attempts = {}
    notified = set()
    paused_apps = set()
    problematic_apps = set()

    while True:
        try:
            print("🔍 Obteniendo aplicaciones de ArgoCD...")  # Mensaje de depuración
            apps = ArgoCDClient.get_applications(timeout=REQUEST_TIMEOUT)

            if not apps:
                print("⚠️ No se encontraron aplicaciones o hubo un error al obtenerlas.")
                time.sleep(30)
                continue

            for app in apps:
                app_name = app.get("metadata", {}).get("name", "Desconocido")
                health_status = app["status"]["health"]["status"]
                sync_status = app["status"]["sync"]["status"]
                current_version = get_app_version(app)

                # Excluir la aplicación 'argocd-monitor' del análisis
                if app_name == "argocd-monitor":
                    print(f"⏩ Excluyendo la aplicación '{app_name}' del análisis.")
                    continue

                print(f"🔄 Procesando la aplicación: {app_name}")  # Mensaje de depuración
                ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)

                if app_name not in attempts:
                    attempts[app_name] = 0

                # Inicializar el estado y la versión si no están registrados
                if app_name not in app_versions:
                    app_versions[app_name] = {"health_status": health_status, "version": current_version}

                # Verificar si el estado o la versión han cambiado
                previous_health_status = app_versions[app_name]["health_status"]
                previous_version = app_versions[app_name]["version"]

                if health_status == "Healthy" and sync_status == "Synced":
                    print(f"✅ '{app_name}' está en estado Healthy y Synced.")
                    if app_name in notified or app_name in paused_apps or app_name in problematic_apps:
                        SlackNotifier.send_notification(app_name, "Healthy", attempts[app_name], "La aplicación volvió a estar Healthy.")
                        notified.discard(app_name)
                        paused_apps.discard(app_name)
                        problematic_apps.discard(app_name)
                    attempts[app_name] = 0
                elif app_name in paused_apps:
                    print(f"⏸️ '{app_name}' está pausada. Monitoreando su estado...")
                elif sync_status == "OutOfSync":
                    print(f"⚠️ '{app_name}' está OutOfSync. Intentando sincronizar...")
                    ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                    attempts[app_name] += 1
                elif health_status in ["Degraded", "Error"]:
                    problematic_apps.add(app_name)
                    if attempts[app_name] < 3:
                        print(f"🔄 Intentando recuperar '{app_name}' (Intento {attempts[app_name] + 1}/3)...")
                        ArgoCDClient.sync_app(app_name, timeout=REQUEST_TIMEOUT)
                        attempts[app_name] += 1
                        time.sleep(10)  # Esperar 10 segundos entre intentos
                    else:
                        if app_name not in notified:
                            print(f"⏸️ '{app_name}' no se pudo recuperar después de 3 intentos. Notificando y pausando...")
                            SlackNotifier.send_notification(app_name, health_status, attempts[app_name], "La aplicación fue pausada después de 3 intentos fallidos.")
                            paused_apps.add(app_name)
                            notified.add(app_name)
                elif health_status in ["Degraded", "Error", "OutOfSync"] and current_version != previous_version:
                    print(f"⚠️ '{app_name}' cambió de estado ({previous_health_status} -> {health_status}) y de versión ({previous_version} -> {current_version}). Iniciando rollback...")
                    rollback_application(app_name)
                    SlackNotifier.send_notification(app_name, health_status, 0, f"Rollback realizado para la versión {current_version}.")
                else:
                    print(f"ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

                # Actualizar el estado y la versión registrados
                app_versions[app_name]["health_status"] = health_status
                app_versions[app_name]["version"] = current_version

            time.sleep(60)

        except Exception as e:
            print(f"❌ Error en el ciclo principal: {e}")
            import traceback
            traceback.print_exc()  # Agregar traza para depuración
            time.sleep(30)

if __name__ == "__main__":
    main()
