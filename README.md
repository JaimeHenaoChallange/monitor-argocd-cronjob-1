# ArgoCD Monitor

## Overview

The ArgoCD Monitor is a Kubernetes-based solution designed to monitor the health and synchronization status of ArgoCD applications. It automatically synchronizes applications and sends notifications to a Slack channel in case of issues. This tool ensures that your applications remain in a healthy state and provides timely alerts for any problems.

---

## Architecture

### High-Level Diagram

```plaintext
+-------------------+       +-------------------+
|                   |       |                   |
|  Kubernetes Cron  |       |   ArgoCD Server   |
|      Job          |       |                   |
|                   |       |                   |
|  +-------------+  |       |  +-------------+  |
|  | monitor.py  |  |       |  | ArgoCD API  |  |
|  +-------------+  |       |  +-------------+  |
|                   |       |                   |
+-------------------+       +-------------------+
          |                           |
          |                           |
          +---------------------------+
                      HTTPS
                       |
                       v
+------------------------------------------------+
|                                                |
|                Slack Webhook                   |
|                                                |
+------------------------------------------------+
```

---

## Features

- **Health Monitoring**: Continuously monitors the health and synchronization status of ArgoCD applications.
- **Automatic Synchronization**: Automatically synchronizes applications that are out of sync.
- **Slack Notifications**: Sends notifications to a Slack channel for degraded or error states.
- **Configurable**: Easily configurable via environment variables and Kubernetes secrets.
- **Retry Mechanism**: Attempts to recover applications up to three times before pausing and notifying.
- **Kubernetes Integration**: Fully integrated with Kubernetes CronJobs for periodic execution.

---

## Installation

### Prerequisites

- Kubernetes cluster with ArgoCD installed.
- Slack Webhook URL for notifications.
- Access to the ArgoCD API with a valid token.

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/JaimeHenaoChallange/opcion2.git
   cd opcion2/scripts/monitor-argocd-cronjob-1
   ```

2. **Apply Kubernetes Manifests**:
   Deploy the required resources (CronJob, ConfigMap, Secrets, etc.) to your Kubernetes cluster:
   ```bash
   kubectl apply -f /workspaces/monitor-2/scripts/monitor-argocd-cronjob-1/
   ```

3. **Verify Deployment**:
   Ensure the CronJob and related resources are running:
   ```bash
   kubectl get cronjob -n poc
   ```

---

## Configuration

### Environment Variables

The following environment variables are required for the monitor to function:

- `ARGOCD_API`: The ArgoCD API endpoint (e.g., `https://argocd-server.argocd.svc.cluster.local/api/v1`).
- `ARGOCD_TOKEN`: The ArgoCD API token stored in a Kubernetes secret.
- `SLACK_WEBHOOK_URL`: The Slack Webhook URL for sending notifications.

### Kubernetes Secrets

The `ARGOCD_TOKEN` should be stored securely in a Kubernetes secret. Example:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: argocd-token-secret
  namespace: poc
type: Opaque
data:
  token: <base64-encoded-token>
```

### ConfigMap

The `ARGOCD_API` endpoint is stored in a ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-monitor-config
  namespace: poc
data:
  ARGOCD_API: "https://argocd-server.argocd.svc.cluster.local/api/v1"
```

---

## Usage

### Monitor Logs

To view the logs of the CronJob:
```bash
kubectl logs -l app.kubernetes.io/name=argocd-monitor -n poc
```

### Test Connectivity

To test connectivity to the ArgoCD API:
```bash
kubectl run -it --rm debug --image=alpine --restart=Never -n poc -- sh
apk add curl
curl -k https://argocd-server.argocd.svc.cluster.local:443/api/v1/applications
```

### Manual Synchronization

To manually synchronize an application in ArgoCD:
```bash
argocd app sync <application-name>
```

---

## Development

### Local Development

1. **Build the Docker Image**:
   ```bash
   docker build -t argocd-monitor .
   ```

2. **Run Locally with Docker Compose**:
   ```bash
   docker-compose up
   ```

3. **Run the Script Directly**:
   Ensure you have Python and dependencies installed:
   ```bash
   pip install -r requirements.txt
   python monitor.py
   ```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
