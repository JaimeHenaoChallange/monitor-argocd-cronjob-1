# ArgoCD Monitor

## Overview

The ArgoCD Monitor is a Kubernetes-based solution designed to monitor the health and synchronization status of ArgoCD applications. It interacts with the ArgoCD API to ensure applications are in a healthy and synchronized state. Notifications are sent to a Slack channel in case of issues, providing timely alerts for degraded or error states.

---

## Architecture

### High-Level Diagram

```plaintext
+-------------------+       +-------------------+
|                   |       |                   |
|   ArgoCD Monitor  |       |   ArgoCD Server   |
|      Script       |       |                   |
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

### Directory Structure Diagram

```plaintext
/workspaces/monitor-2/scripts/monitor-argocd-cronjob-1
├── argocd-monitor.yaml
├── argocd-application.yaml
├── Dockerfile
├── requirements.txt
├── logic/
│   ├── argocd_client.py
│   ├── slack_notifier.py
│   └── config.py
└── monitor.py
```

---

## Features

- **Health Monitoring**: Continuously monitors the health and synchronization status of ArgoCD applications.
- **Automatic Synchronization**: Automatically synchronizes applications that are out of sync.
- **Slack Notifications**: Sends notifications to a Slack channel for degraded or error states.
- **Retry Mechanism**: Attempts to recover applications up to three times before pausing and notifying.
- **Configurable**: Easily configurable via environment variables and Kubernetes secrets.

---

## Directory Structure

The directory contains the following files and subdirectories:

- **`argocd-monitor.yaml`**: Kubernetes manifests for the monitor, including ConfigMaps, Secrets, and Deployment.
- **`argocd-application.yaml`**: ArgoCD Application resource to manage the monitor itself.
- **`Dockerfile`**: Dockerfile for building the monitor's container image.
- **`requirements.txt`**: Python dependencies for the monitor.
- **`logic/`**: Contains Python modules for interacting with ArgoCD and Slack.
  - `argocd_client.py`: Handles communication with the ArgoCD API.
  - `slack_notifier.py`: Sends notifications to Slack.
  - `config.py`: Loads and validates environment variables.
- **`monitor.py`**: Main script for monitoring and managing ArgoCD applications.

---

## Implementation Guide

### Step 1: Build the Docker Image

1. **Navigate to the directory**:
   ```bash
   cd /workspaces/monitor-2/scripts/monitor-argocd-cronjob-1
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t jaimehenao8126/argocd-monitor:latest .
   ```

3. **Verify the image**:
   ```bash
   docker images | grep argocd-monitor
   ```

### Step 2: Push the Image to DockerHub

1. **Log in to DockerHub**:
   ```bash
   docker login
   ```

2. **Push the image**:
   ```bash
   docker push jaimehenao8126/argocd-monitor:latest
   ```

3. **Verify the image on DockerHub**:
   Visit your DockerHub repository to confirm the image is available.

---

## Kubernetes Deployment

### Step 1: Apply Kubernetes Manifests

1. **Apply the namespace, ConfigMap, and Secret**:
   ```bash
   kubectl apply -f argocd-monitor.yaml
   ```

2. **Apply the ArgoCD Application resource**:
   ```bash
   kubectl apply -f argocd-application.yaml
   ```

3. **Verify the deployment**:
   ```bash
   kubectl get pods -n poc
   ```

### Step 2: Monitor Logs

1. **View logs of the monitor**:
   ```bash
   kubectl logs -l app=argocd-monitor -n poc
   ```

2. **Debug issues if necessary**:
   ```bash
   kubectl describe pod <pod-name> -n poc
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
  name: argocd-monitor-secret
  namespace: poc
type: Opaque
data:
  ARGOCD_TOKEN: <base64-encoded-token>
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

## Verifying Connectivity

### Test ArgoCD API Connectivity

To verify connectivity to the ArgoCD API from within the Kubernetes cluster:
```bash
kubectl run -it --rm debug --image=alpine --restart=Never -n poc -- sh
apk add curl
curl -k https://argocd-server.argocd.svc.cluster.local/api/v1/applications
```

If the response contains application data, the connectivity is working correctly.

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
