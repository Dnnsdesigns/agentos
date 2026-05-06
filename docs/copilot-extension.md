# AgentOS GitHub Copilot Extension – Setup & Deployment Guide

This guide walks you through registering the AgentOS Copilot Extension as a
GitHub App and running the extension server so that users can invoke it with
`@agentos` inside any GitHub Copilot Chat surface (VS Code, GitHub.com,
GitHub Mobile).

---

## Prerequisites

* Python 3.8 or later
* A publicly reachable HTTPS endpoint (for production).  For local development
  you can use [ngrok](https://ngrok.com/) or similar tunnelling tools.
* A GitHub account with permission to create GitHub Apps (personal or
  organisation).

---

## 1 – Install the optional dependencies

The Copilot Extension server requires FastAPI, uvicorn, and httpx.  These are
declared as an optional extras group so the zero-dependency core package is
unchanged.

```bash
pip install 'agentos[copilot]'
```

---

## 2 – Create the GitHub App

1. Navigate to **Settings → Developer settings → GitHub Apps → New GitHub App**
   (personal account) or **Organisation settings → Developer settings →
   GitHub Apps → New GitHub App** (organisation).

2. Fill in the required fields:

   | Field | Value |
   |---|---|
   | **GitHub App name** | `agentos-copilot` (or any unique name) |
   | **Homepage URL** | Your deployment URL, e.g. `https://my-server.example.com` |
   | **Callback URL** | `https://my-server.example.com/` |
   | **Webhook URL** | `https://my-server.example.com/` |
   | **Webhook secret** | A strong random string you generate (see below) |

3. Under **Permissions & Events → Account permissions**, set
   **Copilot Chat** → **Read-only** (this enables the Copilot Extension
   capability for the app).

4. Click **Create GitHub App**.  Note the **App ID** shown on the settings
   page.

### Generating a webhook secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output – you will pass it to the server as `--secret`.

---

## 3 – Start the extension server

### Development (no TLS, no signature verification)

```bash
python -m agentos copilot-serve --host 127.0.0.1 --port 3000
```

In a second terminal, expose the local server with ngrok:

```bash
ngrok http 3000
```

Copy the `https://` forwarding URL from ngrok and update the GitHub App's
**Webhook URL** and **Callback URL** to point there.

### Production (with signature verification)

```bash
export WEBHOOK_SECRET="<the secret you generated>"
python -m agentos copilot-serve --host 0.0.0.0 --port 3000 --secret "$WEBHOOK_SECRET"
```

The server binds on port 3000 by default.  Put it behind a reverse proxy (e.g.
nginx, Caddy) that terminates TLS.

### Development auto-reload

```bash
python -m agentos copilot-serve --port 3000 --reload
```

---

## 4 – Install the app on an account or organisation

1. On the GitHub App settings page click **Install App**.
2. Choose the account or organisation and click **Install**.

---

## 5 – Verify in Copilot Chat

In VS Code or on GitHub.com open Copilot Chat and type:

```
@agentos help
```

You should receive a formatted list of available commands.

---

## Available commands

| Command | Description | Example |
|---|---|---|
| `@agentos discover [path]` | Scan a directory for coding standards | `@agentos discover src/` |
| `@agentos spec title="..." [desc="..."] [item="..."]` | Create a specification | `@agentos spec title="Auth feature" desc="OAuth2 login"` |
| `@agentos inject spec=<file> standards=<file>` | Inject discovered standards into a spec | `@agentos inject spec=spec.md standards=standards.json` |
| `@agentos run [agent="..."] [task="..."] code="..."` | Run Python code as an agent task | `@agentos run code="def run(): return 'hello'"` |
| `@agentos help` | Show this help | `@agentos help` |

---

## Programmatic usage

```python
from agentos.copilot import create_app
import uvicorn

app = create_app(secret="my-webhook-secret")
uvicorn.run(app, host="0.0.0.0", port=3000)
```

---

## Environment variables

The server does not read environment variables by default.  Pass configuration
via CLI flags:

| Flag | Description | Default |
|---|---|---|
| `--host` | Bind address | `0.0.0.0` |
| `--port` | TCP port | `3000` |
| `--secret` | Webhook secret (disables sig check if omitted) | *(none)* |
| `--reload` | Enable auto-reload (dev only) | `false` |

---

## Security considerations

* **Always set `--secret` in production** to prevent unauthenticated requests
  from reaching the server.
* The `run` command executes arbitrary user-supplied Python code.  In
  production, run the extension server in an isolated container or sandbox.
* The server does not persist any state between requests.

---

## Deployment on Railway / Fly.io / Render

Any platform that can run a Python process and expose an HTTPS endpoint will
work.  A minimal `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install ".[copilot]"
EXPOSE 3000
CMD ["python", "-m", "agentos", "copilot-serve", "--host", "0.0.0.0", "--port", "3000"]
```

Set the `WEBHOOK_SECRET` environment variable on your platform and update the
`CMD` to include `--secret "$WEBHOOK_SECRET"`.
