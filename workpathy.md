# Django Render Deployment Guide (Workpathy)

This guide contains the step-by-step instructions for deploying your Resume Intelligence Engine to Render.com using a free PostgreSQL database from Neon.tech.

## 1. Setting up the Database (Neon.tech)
Since Render's free PostgreSQL database expires after 90 days, we use Neon for a database that is free forever.

1. Go to **[Neon.tech](https://neon.tech/)** and log in or sign up.
2. Click **New Project**, name it something like `resume-db`, and click **Create Project**.
3. On your project dashboard, look for the **Connection Details** box.
4. Hover over the connection string (it starts with `postgresql://...`) and click the **Copy** icon next to it. *This automatically copies your secure connection URL.*

## 2. Deploying on Render
Because your project already has a perfectly configured `render.yaml` (Blueprint), deployment is mostly automatic!

1. Go to **[Render.com](https://render.com/)** and log in.
2. In the top right corner, click **New** > **Blueprint**.
3. Connect your GitHub account and select your repository.
4. Click **Apply**. Render will read your `render.yaml` file and automatically start building your web service using your `Dockerfile`.

## 3. Adding Environment Variables (Secrets)
Your `render.yaml` automatically configured non-sensitive variables (like `DEBUG=False`). You just need to add your private API keys and database URL.

While Render is building your app:
1. In your Render dashboard, click on your newly created web service.
2. On the left-hand menu, click on **Environment**.
3. Click **Add Environment Variable** and add the following:
   * **Key:** `DATABASE_URL` | **Value:** *(Paste your Neon PostgreSQL connection link here)*
   * **Key:** `HUGGINGFACE_API_KEY` | **Value:** *(Paste your HuggingFace API key here)*
   * **Key:** `GEMINI_API_KEY` | **Value:** *(Paste your Gemini key here, if applicable)*
4. Click **Save Changes**.

## How the Free Tier Works
* **Spin-Down (Sleep Mode):** If your app receives no web traffic for 15 minutes, Render puts it to sleep to save resources.
* **Cold Starts:** If someone visits your site while it is asleep, it will take about 30 to 60 seconds to wake up and load. After that first load, it will be fast again for the next 15+ minutes.
* **Monthly Hours:** You get 750 free hours per month, which is enough to run one web service 24/7 all month without running out.

## Why Background Tasks work on the Free Tier
You might wonder how AI resume parsing works without a Celery worker or Redis instance. Your `settings.py` contains:
```python
CELERY_TASK_ALWAYS_EAGER = True
CHANNEL_LAYERS = {
    'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
}
```
This brilliantly tells Django to run Celery tasks and WebSockets directly in the main web server's memory. This means you do not need to pay for a Redis server or a Celery worker on Render—everything runs self-contained inside your free web service!
