import sys
import os
import time
from logic.argocd_client import ArgoCDClient
from logic.slack_notifier import SlackNotifier

# Agregar el directorio de lógica al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logic"))

REQUEST_TIMEOUT = 10  # Tiempo de espera en segundos

def main():
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
                
                # Excluir la aplicación 'argocd-monitor' del análisis
                if app_name == "argocd-monitor":
                    print(f"⏩ Excluyendo la aplicación '{app_name}' del análisis.")
                    continue

                print(f"🔄 Procesando la aplicación: {app_name}")  # Mensaje de depuración
                ArgoCDClient.refresh_app(app_name, timeout=REQUEST_TIMEOUT)
                health_status, sync_status = ArgoCDClient.get_application_status(app_name, timeout=REQUEST_TIMEOUT)

                if app_name not in attempts:
                    attempts[app_name] = 0

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
                else:
                    print(f"ℹ️ '{app_name}' está en estado desconocido: {health_status}.")

            time.sleep(60)

        except Exception as e:
            print(f"❌ Error en el ciclo principal: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
