# Expense Tracker DevOps Mini-Project

An end-to-end DevOps CI/CD pipeline and observability demonstration project built around a lightweight Flask Expense Tracker application.

---

## 1. Project Overview

### Problem Statement
In modern software engineering, manual testing, containerization, deployment, and infrastructure monitoring are prone to human error, slow release velocity, and operational blind spots. This mini-project demonstrates how to automate code testing, container image building, registry publishing, zero-downtime deployment, and real-time observability using standard DevOps tools.

### Objectives
- Automate testing and verification on every Git commit.
- Containerize the application using standard Docker practices.
- Build and orchestrate a Declarative CI/CD Pipeline using Jenkins.
- Provide end-to-end observability using Prometheus for metric collection and Grafana for visual dashboards.
- Set up real-time alerting for service outages (`AppDown`) and CPU spikes (`HighCPUUsage`).
- Provide an on-demand stress testing endpoint (`/burn`) to simulate workloads for live demonstrations.

### Target Users
- **Developers:** Automated unit and API testing on push with instant feedback.
- **DevOps / SRE Engineers:** Automated builds, registry management, metric monitoring, and alerting.
- **Academic Reviewers / Evaluators:** A clean, reproducible showcase of the complete DevOps lifecycle.

### Functional Requirements
- **Expense Management:** Add, view, edit, and delete expense records (with title, amount, category, date, and calculated total).
- **RESTful API:** Full CRUD operations returning standard HTTP status codes (`200`, `201`, `400`, `404`).
- **Health Check Endpoint:** `GET /health` returning `{"status": "ok"}`.
- **Metrics Endpoint:** `GET /metrics` exposing default Flask metrics (latency, requests) and a custom counter `expenses_added_total`.
- **CPU Burn Endpoint:** `GET /burn?seconds=N` to trigger high CPU usage for demonstration of alerting.

---

## 2. Technology Stack

| Domain | Technology |
|---|---|
| **Application** | Python 3.12, Flask 3.0, SQLite3 (stdlib) |
| **Testing** | pytest, pytest-cov |
| **Metrics** | prometheus-flask-exporter, prometheus_client |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | Jenkins (Declarative Pipeline with Docker CLI integration) |
| **Artifact Registry** | Docker Hub (`piyushkoli04/expense-tracker`) |
| **Monitoring** | Prometheus |
| **Host Metrics** | Prometheus Node Exporter |
| **Visualization** | Grafana (Auto-provisioned Dashboards & Datasource) |
| **API Testing** | Postman (Collection v2.1) |

---

## 3. Architecture & Pipeline Diagram

```text
+---------------------------------------------------------------------------------------+
|                                    DEVELOPER WORKSTATION                              |
|                                                                                       |
|   [ Code Edit ]  --->  [ pytest -v ]  --->  [ git push origin main ]                  |
+-------------------------------------------------------+-------------------------------+
                                                        |
                                                        | Webhook / Polling (ngrok)
                                                        v
+---------------------------------------------------------------------------------------+
|                                  JENKINS CI/CD SERVER                                 |
|                                                                                       |
|   +-------------------+       +------------------------+       +------------------+   |
|   | 1. Checkout SCM   | ----> | 2. Install Deps (venv) | ----> | 3. Build & py_cmp|   |
|   +-------------------+       +------------------------+       +------------------+   |
|                                                                          |            |
|                                                                          v            |
|   +-------------------+       +------------------------+       +------------------+   |
|   | 6. Docker Push    | <---- | 5. Docker Build        | <---- | 4. Test (pytest) |   |
|   |    (Docker Hub)   |       |    (:build & :latest)  |       |    (report.xml)  |   |
|   +---------+---------+       +------------------------+       +------------------+   |
|             |                                                                         |
|             v                                                                         |
|   +---------------------------------------------------+                               |
|   | 7. Deploy: Run container on devops-net & curl /health |                           |
|   +---------------------------------------------------+                               |
+------------------------------------------+--------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                          DOCKER NETWORK: devops-net                                   |
|                                                                                       |
|   +---------------------------------------+       +-------------------------------+   |
|   |        expense-app (Port 5000)        |       |    node-exporter (Port 9100)  |   |
|   |  - Web UI (/)                         |       |  - Host CPU / Mem / Disk / Net|   |
|   |  - API (/api/expenses)                |       +---------------+---------------+   |
|   |  - Metrics (/metrics)                 |                       |                   |
|   +-------------------+-------------------+                       |                   |
|                       ^                                           |                   |
|                       | Scrapes (15s)                             | Scrapes (15s)     |
|                       +---------------------+  +------------------+                   |
|                                             |  |                                      |
|                                       +-----+--v-----+                                |
|                                       |  Prometheus  | (Port 9090)                    |
|                                       | (AlertRules) |                                |
|                                       +-------+------+                                |
|                                               | Queries                               |
|                                               v                                       |
|                                       +--------------+                                |
|                                       |   Grafana    | (Port 3000)                    |
|                                       | (Dashboards) |                                |
|                                       +--------------+                                |
+---------------------------------------------------------------------------------------+
```

---

## 4. Service URLs & Ports Reference

| Service | Container Name | URL | Default Credentials |
|---|---|---|---|
| **Expense Tracker App** | `expense-app` | [http://localhost:5000](http://localhost:5000) | N/A |
| **Jenkins CI/CD** | `jenkins` | [http://localhost:8080](http://localhost:8080) | Initial admin password (see below) |
| **Prometheus** | `prometheus` | [http://localhost:9090](http://localhost:9090) | N/A |
| **Grafana** | `grafana` | [http://localhost:3000](http://localhost:3000) | `admin` / `admin` |
| **Node Exporter** | `node-exporter` | [http://localhost:9100/metrics](http://localhost:9100/metrics) | N/A |

---

## 5. How to Run Locally

### 5.1 Python Virtual Environment & Testing

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux / macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the unit & integration test suite:
   ```bash
   pytest -v
   ```

4. Start the application locally:
   ```bash
   python app.py
   ```
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

### 5.2 Standalone Docker Container

1. Build the Docker image:
   ```bash
   docker build -t expense-tracker:local .
   ```

2. Run the container:
   ```bash
   docker run -d --name expense-app -p 5000:5000 -v expense-data:/data expense-tracker:local
   ```

3. Verify health endpoint:
   ```bash
   curl http://localhost:5000/health
   ```

---

## 6. How to Start the Infrastructure (Docker Compose)

The monitoring and CI/CD tools run as isolated services connected via the `devops-net` bridge network.

1. Navigate to the project root and start the infrastructure:
   ```bash
   docker compose -f infra/docker-compose.yml up -d --build
   ```

2. Verify all containers are running:
   ```bash
   docker compose -f infra/docker-compose.yml ps
   ```

3. Services launched:
   - `jenkins` on `:8080` and `:50000`
   - `prometheus` on `:9090`
   - `node-exporter` on `:9100`
   - `grafana` on `:3000`

---

## 7. Jenkins Setup Steps

1. **Retrieve Initial Admin Password:**
   ```bash
   docker exec -it jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

2. **Access Jenkins:**
   - Open [http://localhost:8080](http://localhost:8080).
   - Paste the admin password.
   - Click **Install Suggested Plugins**.
   - Create your administrator user and complete the wizard.

3. **Install Required Plugins:**
   - Go to **Manage Jenkins** -> **Plugins** -> **Available Plugins**.
   - Search and install:
     - **Docker Pipeline**
     - **JUnit Plugin** (usually installed by default)
     - **GitHub Integration Plugin**
   - Restart Jenkins if prompted.

4. **Add Docker Hub Credentials:**
   - Go to **Manage Jenkins** -> **Credentials** -> **System** -> **Global credentials (unrestricted)**.
   - Click **Add Credentials**.
   - Kind: **Username with password**.
   - Username: `piyushkoli04` (or your Docker Hub username).
   - Password: `<Your Docker Hub Personal Access Token or Password>`.
   - ID: `dockerhub-creds` *(Exact ID required by Jenkinsfile)*.
   - Click **Create**.

5. **Create the Pipeline Job:**
   - Click **New Item**.
   - Enter name: `expense-tracker-pipeline`.
   - Select **Pipeline** and click **OK**.
   - Under **Build Triggers**, check **GitHub hook trigger for GITScm polling** and **Poll SCM** (`H/5 * * * *`).
   - Under **Pipeline**, set Definition to **Pipeline script from SCM**.
   - SCM: **Git**.
   - Repository URL: `https://github.com/PiyushKoli04/expense-tracker-devops.git` (or your repo URL).
   - Branch Specifier: `*/main` (or `*/master`).
   - Script Path: `Jenkinsfile`.
   - Click **Save**.

---

## 8. Webhook Setup (ngrok for Local Demo)

To allow GitHub to trigger Jenkins running on your local machine:

1. Download and start ngrok on port 8080:
   ```bash
   ngrok http 8080
   ```
2. Copy the public forwarding HTTPS URL (e.g., `https://abcd-1234.ngrok-free.app`).
3. In your GitHub repository:
   - Navigate to **Settings** -> **Webhooks** -> **Add webhook**.
   - Payload URL: `https://<YOUR-NGROK-URL>/github-webhook/` *(Notice trailing slash)*.
   - Content type: `application/json`.
   - Which events: **Just the push event**.
   - Click **Add webhook**.

---

## 9. Live Demo Walkthrough Script

Follow these steps for a complete project presentation:

### Step 1: Baseline Verification
1. Open Grafana at [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`).
2. Go to **Dashboards** -> **Expense Tracker DevOps**.
3. Verify panels are loaded and live (Application Availability shows `UP` once deployed).

### Step 2: Trigger CI/CD via Code Push
1. Make a visible change in `templates/index.html` (e.g. modify the header or button).
2. Commit and push:
   ```bash
   git add .
   git commit -m "feat: enhance UI for demo presentation"
   git push origin main
   ```
3. Switch to Jenkins ([http://localhost:8080](http://localhost:8080)).
4. Watch the pipeline automatically trigger and progress through the 7 stages:
   - **Checkout** -> **Install Dependencies** -> **Build** -> **Test** -> **Docker Build** -> **Docker Push** -> **Deploy**.
5. Check the test report tab under the build to show JUnit test results.

### Step 3: Verify Deployed Application
1. Visit [http://localhost:5000](http://localhost:5000).
2. Add a new expense (e.g., `Lunch`, `$15.00`, `Food`, `2026-03-30`).
3. Notice the updated total and list.

### Step 4: Verify Prometheus & Grafana Metrics
1. Open [http://localhost:5000/metrics](http://localhost:5000/metrics) to show raw Prometheus metrics.
2. In Grafana:
   - **Expenses Added Total** increases by 1.
   - **Request Rate** and **Request Latency** reflect traffic.

### Step 5: Simulate CPU Alerting (`/burn`)
1. In Prometheus ([http://localhost:9090/alerts](http://localhost:9090/alerts)), show the alert rule `HighCPUUsage`.
2. Trigger high CPU burn:
   ```bash
   curl "http://localhost:5000/burn?seconds=65"
   ```
3. Watch the Grafana dashboard:
   - The **CPU Usage %** gauge turns red (> 80%).
4. In Prometheus ([http://localhost:9090/alerts](http://localhost:9090/alerts)):
   - State transitions from **Inactive** -> **Pending** -> **Firing**.

### Step 6: Simulate Service Outage (`AppDown`)
1. Stop the application container:
   ```bash
   docker stop expense-app
   ```
2. In Grafana:
   - **Application Availability** switches to `DOWN` (Red).
3. In Prometheus:
   - `AppDown` alert transitions to **Firing** after 30 seconds.
4. Recover service:
   ```bash
   docker start expense-app
   ```
5. Application Availability recovers to `UP`.
