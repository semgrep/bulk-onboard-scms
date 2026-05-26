# Bulk-onboard SCM providers to Semgrep

This tool connects many source-code organizations (Bitbucket workspaces, Azure DevOps orgs, GitLab groups, etc.) to Semgrep at once, so Semgrep can scan the repositories inside them. Instead of adding each one in the Semgrep UI, you list them in a YAML file and run a single command.

Supported providers:

- Bitbucket Cloud (`bitbucket`)
- Bitbucket Data Center (`bitbucket_data_center`)
- Azure DevOps (`azure_devops`)
- GitLab Cloud (`gitlab`)
- GitLab Self-Managed (`gitlab_self_managed`)

After it runs, each listed namespace will appear as a connected source in Semgrep.

---

## Before you start

You will need:

1. **Python 3.10 or newer** installed. Check with `python3 --version`.
2. **A terminal.** macOS/Linux: Terminal. Windows: use WSL or Git Bash (the `source` command below won't work in plain PowerShell).
3. **Three pieces of information**, described below.

### 1. Your Semgrep deployment ID

Log in to Semgrep at https://semgrep.dev and go to **Settings → Deployment**. The numeric ID is shown there (and in the URL).

### 2. A Semgrep API token

In Semgrep, go to **Settings → Tokens** and create a new token with permission to manage SCM configurations. Copy it somewhere safe — you won't be able to see it again.

### 3. An access token for your SCM provider

Create a personal/HTTP access token in your SCM with **read** access to every namespace you plan to onboard:

| Provider                | Where to create the token                                      |
|-------------------------|----------------------------------------------------------------|
| Bitbucket Cloud         | Personal settings → App passwords (or workspace access token)  |
| Bitbucket Data Center   | Profile → HTTP access tokens                                   |
| Azure DevOps            | User settings → Personal access tokens                         |
| GitLab (cloud/self-mg.) | Preferences → Access tokens (or a Group access token)          |

---

## Step 1 — Install

Open a terminal in this folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(If you already use [`uv`](https://docs.astral.sh/uv/), you can substitute `uv venv` and `uv pip install -r requirements.txt`.)

## Step 2 — Build your YAML file

The YAML tells the tool **which provider** to use, **which base URL** to talk to (for self-hosted servers), and **which namespaces** to onboard.

A *namespace* is the per-provider unit Semgrep onboards:

| Provider                | Namespace meaning              |
|-------------------------|--------------------------------|
| `bitbucket`             | Workspace slug                 |
| `bitbucket_data_center` | Project key                    |
| `azure_devops`          | Organization name              |
| `gitlab` / self-managed | Group (or `group/subgroup`)    |

Example (Bitbucket Data Center):

```yaml
provider: bitbucket_data_center
base_url: https://bitbucket.example.com
bitbucket_project_keys:
  - ABC
  - DEF
```

Ready-made examples for every supported provider live in `examples/` — copy the one that matches your provider and edit the namespace list.

Notes:
- `base_url` is **required** for self-hosted providers (Bitbucket Data Center, GitLab Self-Managed, Azure DevOps). For Bitbucket Cloud and GitLab Cloud you can omit it.
- No trailing slash on `base_url`.

## Step 3 — Run

Paste the three values from "Before you start" into this block, then run it in your terminal:

```bash
export SEMGREP_DEPLOYMENT_ID=12345
export SEMGREP_API_TOKEN=your_semgrep_api_token
export SCM_ACCESS_TOKEN=your_scm_pat

python bulk_onboard_scms.py examples/bitbucket_data_center.yaml
```

These `export` lines only last for the current terminal window. If you close it, you'll need to set them again.

(For ad-hoc runs you can put `access_token: …` directly in the YAML instead of using `SCM_ACCESS_TOKEN`, but the env var is preferred so tokens don't end up in files.)

---

## What you'll see

One line per namespace:

```
[OK]   Created ScmConfig for bitbucket_data_center namespace: ABC
[FAIL] Failed to create ScmConfig for bitbucket_data_center namespace: DEF — 401 ...
```

## Troubleshooting

- **`Missing required env var(s)`** — you didn't set `SEMGREP_API_TOKEN` or `SEMGREP_DEPLOYMENT_ID` in this terminal session.
- **`401 Unauthorized`** — your `SEMGREP_API_TOKEN` is wrong, expired, or lacks SCM permissions.
- **`403 Forbidden`** — the SCM access token can't see that namespace. Check its scope.
- **`404 Not Found`** — the `SEMGREP_DEPLOYMENT_ID` is wrong, or the namespace doesn't exist on the SCM.
- **`'base_url' is required`** — your provider is self-hosted; add `base_url:` to the YAML.
- **Duplicate entries on re-run** — re-running may create a second config for the same namespace. Check Semgrep before running again.

## Verify

Open Semgrep → **Settings → Source code managers**. Each namespace from your YAML file should be listed.
