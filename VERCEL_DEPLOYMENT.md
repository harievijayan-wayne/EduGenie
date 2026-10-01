# Deploying EduGenie to Vercel

EduGenie is configured to deploy seamlessly to [Vercel](https://vercel.com) as a serverless Python FastAPI application.

---

## Method 1: Deploy via GitHub (Recommended)

1. **Commit and Push your project to GitHub:**
   ```bash
   git add .
   git commit -m "Configure project for Vercel deployment"
   git push origin main
   ```

2. **Import to Vercel:**
   - Go to your [Vercel Dashboard](https://vercel.com/dashboard).
   - Click **"Add New..."** → **"Project"**.
   - Select your GitHub repository.
   - Leave the **Framework Preset** as **"Other"** (or auto-detected).
   - Leave the Root Directory as `./`.

3. **Configure Environment Variables (in Vercel Project Settings):**
   Add the following environment variables under **Settings > Environment Variables**:

   | Variable | Example Value | Description |
   | :--- | :--- | :--- |
   | `AI_BACKEND` | `groq` | Recommended AI backend for cloud deployment (`groq` or `demo`) |
   | `GROQ_API_KEY` | `gsk_...` | Your Groq Cloud API key ([Get free key](https://console.groq.com/keys)) |
   | `SECRET_KEY` | `your-random-32-char-secret-string` | JWT security secret key |
   | `DATABASE_URL` | *(Optional)* | Cloud PostgreSQL database (e.g. Supabase, Neon). If omitted, automatically uses SQLite in `/tmp`. |

4. **Click "Deploy"**:
   - Vercel will build the serverless functions, install dependencies, and publish your URL (e.g., `https://edugenie.vercel.app`).

---

## Method 2: Deploy via Vercel CLI

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Log in to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from the project root**:
   ```bash
   vercel
   ```
   Follow the prompts to link your project.

4. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

---

## Architecture on Vercel

- **FastAPI Framework Detection**: Vercel natively detects FastAPI through `pyproject.toml` (`[tool.vercel] entrypoint = "backend.main:app"`) and root `main.py`.
- **Routing**: Handled natively by Vercel's FastAPI integration without needing manual rewrite rules.
- **Static Assets & Jinja2 Templates**: Served directly by FastAPI using absolute paths resolved at runtime.
- **Filesystem & Database**:
  - In Vercel's serverless environment, the root filesystem is read-only.
  - EduGenie automatically detects Vercel (`IS_VERCEL=1`), copies the seed database to `/tmp/edugenie.db`, and stores temporary file uploads in `/tmp/uploads`.
  - For persistent multi-user production data, simply set `DATABASE_URL` to a cloud PostgreSQL database (e.g. Supabase, Neon, Railway).

