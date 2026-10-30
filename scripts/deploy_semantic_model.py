"""Deploy the TMDL semantic model in powerbi/ to a Fabric workspace.

Creates the semantic model, or updates its definition if one with the same
name exists, then refreshes it so Direct Lake picks up the current Gold tables.
Authenticates as the signed-in Azure CLI account (`az login`).

Usage:
    python scripts/deploy_semantic_model.py --workspace-id <id>
"""

from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from azure.identity import AzureCliCredential


FABRIC_API = "https://api.fabric.microsoft.com/v1"
POWER_BI_API = "https://api.powerbi.com/v1.0/myorg"
MODEL_DIRECTORY = Path("powerbi/sm_retail_commercial.SemanticModel")
MODEL_NAME = "sm_retail_commercial"

credential = AzureCliCredential()


def request(method: str, url: str, scope: str, body: dict | None = None):
    token = credential.get_token(scope).token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as response:
            payload = response.read()
            return response.status, response.headers, json.loads(payload) if payload else None
    except urllib.error.HTTPError as error:
        raise SystemExit(f"{method} {url} failed with {error.code}: {error.read().decode()}") from None


def fabric(method: str, path: str, body: dict | None = None):
    return request(method, f"{FABRIC_API}{path}", "https://api.fabric.microsoft.com/.default", body)


def wait_for_operation(headers) -> None:
    """Poll a Fabric long-running operation until it finishes."""
    location = headers.get("Location")
    while location:
        time.sleep(int(headers.get("Retry-After", 5)))
        _, headers, state = request("GET", location, "https://api.fabric.microsoft.com/.default")
        status = (state or {}).get("status")
        if status == "Failed":
            raise SystemExit(f"Operation failed: {json.dumps(state, indent=2)}")
        if status in ("Succeeded", None):
            return


def definition() -> dict:
    parts = [
        {
            "path": path.relative_to(MODEL_DIRECTORY).as_posix(),
            "payload": base64.b64encode(path.read_bytes()).decode(),
            "payloadType": "InlineBase64",
        }
        for path in sorted(MODEL_DIRECTORY.rglob("*"))
        if path.is_file()
    ]
    return {"parts": parts}


def find_model(workspace_id: str) -> str | None:
    _, _, models = fabric("GET", f"/workspaces/{workspace_id}/semanticModels")
    return next((m["id"] for m in models["value"] if m["displayName"] == MODEL_NAME), None)


def refresh(workspace_id: str, model_id: str) -> None:
    scope = "https://analysis.windows.net/powerbi/api/.default"
    base = f"{POWER_BI_API}/groups/{workspace_id}/datasets/{model_id}/refreshes"
    request("POST", base, scope, {"type": "full"})
    while True:
        time.sleep(5)
        _, _, history = request("GET", f"{base}?$top=1", scope)
        latest = history["value"][0]
        if latest["status"] != "Unknown":  # Unknown means still running
            print(f"Refresh {latest['status']}")
            if latest["status"] != "Completed":
                raise SystemExit(json.dumps(latest, indent=2))
            return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace-id", required=True)
    args = parser.parse_args()

    model_id = find_model(args.workspace_id)
    if model_id:
        _, headers, _ = fabric(
            "POST",
            f"/workspaces/{args.workspace_id}/semanticModels/{model_id}/updateDefinition",
            {"definition": definition()},
        )
        wait_for_operation(headers)
        print(f"Updated {MODEL_NAME} ({model_id})")
    else:
        _, headers, _ = fabric(
            "POST",
            f"/workspaces/{args.workspace_id}/semanticModels",
            {"displayName": MODEL_NAME, "definition": definition()},
        )
        wait_for_operation(headers)
        model_id = find_model(args.workspace_id)
        print(f"Created {MODEL_NAME} ({model_id})")

    refresh(args.workspace_id, model_id)


if __name__ == "__main__":
    main()
