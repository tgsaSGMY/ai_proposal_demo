# 🚀 AI Proposal Platform: Dev VPS & CI/CD Master Guide

Welcome to the comprehensive guide for the AI Proposal Platform's Beta/Dev environment. This document is designed to walk future developers through how the VPS is structured, how to access it securely, and how the automated deployment pipeline works.

---

## 1. System Overview & Hardware
This environment simulates our live production server but operates under strict hardware constraints to facilitate rigorous stress testing.

* **Hardware Specs:** 1 vCPU, 2GB RAM, 50GB Storage.
* **Mitigation:** A **4GB Swap file** is actively running to prevent the memory-heavy Supabase instance from crashing the system.
* **Routing:** All web traffic is routed through **Nginx Proxy Manager (NPM)** using `nip.io` wildcard domains.

---

## 2. Directory Structure Visualization

To understand how the server operates, here is the visual layout of the `/opt/` directory on the Dev VPS, where all Docker applications live.

```text
/opt/
├── proxy/                           # 🌐 Nginx Proxy Manager (Global Router)
│   ├── data/                        # NPM internal routing rules
│   ├── letsencrypt/                 # Auto-generated SSL Certificates
│   └── docker-compose.yml           # Runs on ports 80/443 & network: npm-network
│
└── projects/                        # 📦 All Application Code & Databases
    │
    ├── supabase-project/            # 🗄️ Shared Database Infrastructure
    │   ├── volumes/                 # Persistent DB storage & user file uploads
    │   └── docker-compose.yml       # Exposes network: supabase_default
    │
    └── ai-proposal-platform/        # 💻 Our Main Application (Cloned from GitHub)
        ├── frontend/
        │   └── .env                 # Run-time fallback secrets
        ├── backend/
        │   └── .env                 # CRITICAL: Contains Dev OAuth Callback URL
        └── docker-compose.beta.yml  # Dev deployment script (Uses :dev image tags)
```

> **💡 Why this structure?** Separating the Proxy, Database, and Application allows us to restart the app without restarting the heavy database, saving crucial RAM.

---

## 3. Server Access & Security Guide

For security, password authentication is completely disabled on this VPS. Access is strictly managed via SSH keys.

### Who has access?
1. **Developers (You):** Your personal SSH public key is in `/root/.ssh/authorized_keys`.
2. **GitHub Actions (CI/CD Bot):** A dedicated `github-actions-dev` key pair exists. The private key is in GitHub Secrets, allowing the automated pipeline to deploy code.
3. **The VPS Itself:** The VPS holds a "Deploy Key" (`github_deploy_key`) which has read-only access to our private GitHub repository, allowing it to execute `git clone`.

### 🔒 How to Access the Database UI (Supabase Studio)
To prevent unauthorized access, the database dashboard is **not** exposed to the public internet. You must use an **SSH Tunnel** to view it on your local machine.

**Step-by-step:**
1. Open your local computer's terminal.
2. Create the secure tunnel by running:
   ```bash
   ssh -L 3000:localhost:3000 root@<DEV_VPS_IP>
   ```
3. Leave that terminal window open.
4. Open your web browser and go to: `http://localhost:3000`
5. You are now securely viewing the Dev database!

---

## 4. The CI/CD Pipeline (How Code Goes Live)

We use GitHub Actions to completely automate deployments. You never need to build images locally or SSH into the server manually to deploy updates.

**The Workflow File:** `.github/workflows/deploy-dev.yml`

### What happens when you push to the `dev` branch?
1. **Build:** GitHub spins up a temporary server, downloads your code, and injects your Build-Time secrets (like Supabase URLs).
2. **Package:** It compiles the Nuxt frontend and FastAPI backend into Docker images.
3. **Publish:** It pushes these images to Docker Hub under `tgsataiwan/*:dev`.
4. **Deploy:** It securely SSHs into the Dev VPS, pulls the latest compose configuration, downloads the new `:dev` images, and restarts the containers automatically.

---

## 5. Secrets Management Guide (The "Gotchas")

Managing `.env` variables is the most common source of bugs. We split secrets into two categories: **Build-Time** and **Run-Time**.

### 🛠️ Build-Time Secrets (Configured in GitHub)
Nuxt 3 "bakes" public variables into the Javascript code when compiling. Because compilation happens on GitHub, these **must** be stored in **GitHub Repo -> Settings -> Secrets -> Actions**:
* `SUPABASE_URL`
* `SUPABASE_ANON_KEY`
* `NUXT_PUBLIC_API_BASE_URL` *(Must be `https://api-dev.<VPS_IP>.nip.io` so the frontend knows where the backend is!)*
* `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `DEV_VPS_IP`, `DEV_VPS_SSH_KEY`

### ⚙️ Run-Time Secrets (Configured on the VPS)
These files live permanently on the server (`/opt/projects/ai-proposal-platform/backend/.env`) and are **ignored by Git**. They override settings so the Dev server behaves differently than Live.

* **Backend Environment Variables:**
  The `DATABASE_URL` must point to the internal Docker container (`supabase-db`), not an external cloud URL. The OAuth callback must point to your Dev domain.
  ```env
  # Inside backend/.env on the VPS
  DATABASE_URL=postgresql://postgres:{PASSWORD}@supabase-db:5432/postgres
  SUPABASE_URL=http://supabase-kong:8000
  SUPABASE_SERVICE_KEY={LIVE_SERVICE_KEY}
  EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL=https://ai-dev.<VPS_IP>.nip.io/external-auth-callback
  ```

* **Supabase Environment Variables:**
  The `/opt/projects/supabase-project/.env` file MUST be manually updated to include your Dev domain in the CORS rules, otherwise Supabase will block login requests.
  ```env
  SITE_URL="https://ai-dev.<VPS_IP>.nip.io"
  ADDITIONAL_CORS_ORIGINS="http://localhost:3000,https://ai-dev.<VPS_IP>.nip.io"
  ```
> **⚠️ Important:** If you need to allow a new frontend domain to connect to the backend, you must update the CORS `allow_origins` list directly in the codebase (`backend/app/main.py`), NOT in an `.env` file.

---

## 6. Expanding the Server (Adding New Projects)

This VPS is designed to host multiple test projects using a **Shared Database Architecture**.

**Why Shared?** Supabase requires ~2GB of RAM to run. We cannot physically run a second Supabase instance on this machine.

**How to add a new project (e.g., `crm-tool`):**
1. Create a new directory: `mkdir /opt/projects/crm-tool/`
2. Create your `docker-compose.beta.yml` for the new project.
3. **The Magic Step:** In your compose file, attach your backend to the existing networks:
   ```yaml
   networks:
     - npm-network        # Connects to the public Nginx Proxy
     - supabase_default   # Connects to the shared database!
   ```
4. Update the **Supabase CORS**: You must edit `/opt/projects/supabase-project/.env` to add your new domain (`crm-dev...nip.io`) to `ADDITIONAL_CORS_ORIGINS`, then restart `supabase-auth`.
5. Log into the NPM Dashboard (`http://<DEV_VPS_IP>:81`) and create a new proxy route for `crm-dev...nip.io` pointing to your new container.

---

## 7. Future Warnings & Maintenance

1. **The RAM Bottleneck:** The server relies heavily on its Swap file. Do not run heavy background AI data-processing tasks concurrently, or the Linux kernel's OOM (Out Of Memory) killer will terminate your containers.
2. **Merging to Main is Safe:** When you merge the `dev` branch into `main`, the `docker-compose.beta.yml` and GitHub Actions files will carry over. This is 100% safe. The Live server defaults to `docker-compose.yml`, so it will naturally ignore the beta configurations.
3. **Storage Limits:** Docker images take up a lot of space. The CI/CD pipeline automatically runs `docker image prune -f` after every deployment, but keep an eye on the 50GB storage limit using `df -h` periodically.
