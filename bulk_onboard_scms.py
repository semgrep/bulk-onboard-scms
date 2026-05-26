#!/usr/bin/env python3
"""Bulk-add SCM configs to Semgrep for Bitbucket Cloud, Bitbucket Data Center,
Azure DevOps, or GitLab (cloud or self-managed)."""

import os
import sys
import yaml
import requests

SEMGREP_API_BASE = "https://semgrep.dev/api/scm/deployments"
SEMGREP_API_TOKEN = os.environ.get("SEMGREP_API_TOKEN")
SEMGREP_DEPLOYMENT_ID = os.environ.get("SEMGREP_DEPLOYMENT_ID")

HTTP_TIMEOUT = (5, 30)  # (connect, read) seconds

# Default base URLs for cloud SCMs. Azure DevOps is intentionally omitted: the
# baseUrl Semgrep expects typically embeds the org (https://dev.azure.com/{org}),
# so the YAML must specify it explicitly.
DEFAULT_BASE_URLS = {
    "bitbucket": "https://bitbucket.org",
    "gitlab": "https://gitlab.com",
}

# Maps the YAML `provider` value to the Semgrep SCM_TYPE enum string.
PROVIDER_TO_SCM_TYPE = {
    "bitbucket": "SCM_TYPE_BITBUCKET",
    "bitbucket_data_center": "SCM_TYPE_BITBUCKET_DATACENTER",
    "azure_devops": "SCM_TYPE_AZURE_DEVOPS",
    "gitlab": "SCM_TYPE_GITLAB",
    "gitlab_self_managed": "SCM_TYPE_GITLAB_SELFMANAGED",
}

# Each provider stores its namespace list under a provider-specific key in the YAML.
PROVIDER_NAMESPACE_KEY = {
    "bitbucket": "bitbucket_workspaces",
    "bitbucket_data_center": "bitbucket_project_keys",
    "azure_devops": "azure_devops_organizations",
    "gitlab": "gitlab_groups",
    "gitlab_self_managed": "gitlab_groups",
}


def load_config(path: str) -> tuple[str, str, str, list[str]]:
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        print(
            "Invalid YAML: top-level must be a mapping with a 'provider' key "
            "and a namespace list. See examples/."
        )
        sys.exit(1)

    provider = data.get("provider")
    if provider not in PROVIDER_TO_SCM_TYPE:
        print(
            f"Invalid or missing 'provider'. Must be one of: "
            f"{sorted(PROVIDER_TO_SCM_TYPE)}"
        )
        sys.exit(1)

    # Self-managed providers must specify a base_url; cloud ones may override.
    base_url = data.get("base_url") or DEFAULT_BASE_URLS.get(provider)
    if not base_url:
        print(f"'base_url' is required in the YAML for provider '{provider}'.")
        sys.exit(1)

    # Token: env var preferred, but YAML fallback supported for ad-hoc runs.
    token = os.environ.get("SCM_ACCESS_TOKEN") or data.get("access_token")
    if not token:
        print("SCM_ACCESS_TOKEN env var (or 'access_token' in YAML) is required.")
        sys.exit(1)

    namespace_key = PROVIDER_NAMESPACE_KEY[provider]
    namespaces = data.get(namespace_key) or data.get("namespaces") or []
    if not namespaces:
        print(f"No namespaces found under '{namespace_key}' or 'namespaces'.")
        sys.exit(1)

    return provider, base_url, token, namespaces


def create_scm_config(
    provider: str, base_url: str, token: str, namespace: str
) -> None:
    url = f"{SEMGREP_API_BASE}/{SEMGREP_DEPLOYMENT_ID}/configs"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {SEMGREP_API_TOKEN}",
        "content-type": "application/json",
    }
    payload = {
        "type": PROVIDER_TO_SCM_TYPE[provider],
        "namespace": namespace,
        "baseUrl": base_url,
        "accessToken": token,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=HTTP_TIMEOUT)

    if resp.ok:
        print(f"[OK]   Created ScmConfig for {provider} namespace: {namespace}")
    else:
        print(
            f"[FAIL] Failed to create ScmConfig for {provider} namespace: {namespace} "
            f"— {resp.status_code} {resp.text}"
        )


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <config.yaml>")
        sys.exit(1)

    missing = [
        name
        for name, val in (
            ("SEMGREP_API_TOKEN", SEMGREP_API_TOKEN),
            ("SEMGREP_DEPLOYMENT_ID", SEMGREP_DEPLOYMENT_ID),
        )
        if not val
    ]
    if missing:
        print(f"Missing required env var(s): {', '.join(missing)}")
        sys.exit(1)

    provider, base_url, token, namespaces = load_config(sys.argv[1])
    print(
        f"Loaded {len(namespaces)} {provider} namespace(s) (base_url={base_url}). "
        f"Creating SCM configs...\n"
    )

    for ns in namespaces:
        create_scm_config(provider, base_url, token, ns)

    print("\nDone.")


if __name__ == "__main__":
    main()
