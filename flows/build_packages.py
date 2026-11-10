"""Build Power Automate legacy import packages (.zip) from the flow definitions in this folder.

Usage:  python3 flows/build_packages.py
Output: flows/dist/<flow-folder>.zip  ->  Power Automate > My flows > Import > Import Package (Legacy)

Each flow folder contains only definition.json (the workflow definition). This script wraps it
with the manifest files Power Automate expects. Office 365 Outlook is set to "Invoker", so it is
"Provided by run-only user": mail is sent from the mailbox of the colleague who runs the flow.
SharePoint uses the flow owner's connection.
"""
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"

FLOWS = {
    "marketing-campaign": {
        "displayName": "Marketing campaign",
        "description": "Sends a campaign from the Campaigns list (SharePoint) through the runner's Outlook mailbox. Modes: Test / Send.",
    },
    "marketing-campaign-sync-replies": {
        "displayName": "Marketing campaign - Sync replies",
        "description": "Marks campaign recipients who replied and adds unsubscribe replies to the Suppression list.",
    },
}

CONNECTORS = {
    "shared_sharepointonline": {"displayName": "SharePoint", "source": "Embedded",
        "icon": "https://connectoricons-prod.azureedge.net/releases/v1.0.1676/1.0.1676.3617/sharepointonline/icon.png"},
    "shared_office365": {"displayName": "Office 365 Outlook", "source": "Invoker",
        "icon": "https://connectoricons-prod.azureedge.net/releases/v1.0.1676/1.0.1676.3617/office365/icon.png"},
}


def ns_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "feel-it/" + "/".join(parts)))


def build(folder: str, meta: dict) -> Path:
    definition = json.loads((HERE / folder / "definition.json").read_text())
    flow_id = ns_id(folder, "flow")
    flow_res = ns_id(folder, "flow-res")

    resources = {
        flow_res: {
            "id": f"/providers/Microsoft.Flow/flows/{flow_id}",
            "name": flow_id,
            "type": "Microsoft.Flow/flows",
            "suggestedCreationType": "New",
            "creationType": "Existing, New, Update",
            "details": {"displayName": meta["displayName"]},
            "configurableBy": "User",
            "hierarchy": "Root",
            "dependsOn": [],
        }
    }
    apis_map, connections_map, connection_refs = {}, {}, {}
    for key, c in CONNECTORS.items():
        api_res, conn_res = ns_id(folder, key, "api"), ns_id(folder, key, "conn")
        api_id = f"/providers/Microsoft.PowerApps/apis/{key}"
        resources[api_res] = {
            "id": api_id, "name": key, "type": "Microsoft.PowerApps/apis",
            "suggestedCreationType": "Existing",
            "details": {"displayName": c["displayName"], "iconUri": c["icon"]},
            "configurableBy": "System", "hierarchy": "Child", "dependsOn": [],
        }
        resources[conn_res] = {
            "type": "Microsoft.PowerApps/apis/connections",
            "suggestedCreationType": "Existing", "creationType": "Existing",
            "details": {"displayName": c["displayName"], "iconUri": c["icon"]},
            "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_res],
        }
        resources[flow_res]["dependsOn"] += [api_res, conn_res]
        apis_map[key] = api_res
        connections_map[key] = conn_res
        connection_refs[key] = {"connectionName": key, "source": c["source"], "id": api_id, "tier": "NotSpecified"}

    package_manifest = {
        "schema": "1.0",
        "details": {
            "displayName": meta["displayName"],
            "description": meta["description"],
            "createdTime": datetime.now(timezone.utc).isoformat(),
            "packageTelemetryId": ns_id(folder, "telemetry"),
            "creator": "N/A",
            "sourceEnvironment": "",
        },
        "resources": resources,
    }
    flow_definition = {
        "name": flow_id,
        "id": f"/providers/Microsoft.Flow/flows/{flow_id}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": meta["displayName"],
            "definition": definition,
            "connectionReferences": connection_refs,
            "flowFailureAlertSubscribed": False,
            "isManaged": False,
        },
    }

    DIST.mkdir(exist_ok=True)
    out = DIST / f"{folder}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(package_manifest, indent=2))
        z.writestr("Microsoft.Flow/flows/manifest.json",
                   json.dumps({"packageSchemaVersion": "1.0", "flowAssets": {"assetPaths": [flow_id]}}, indent=2))
        base = f"Microsoft.Flow/flows/{flow_id}/"
        z.writestr(base + "definition.json", json.dumps(flow_definition, indent=2, ensure_ascii=False))
        z.writestr(base + "apisMap.json", json.dumps(apis_map, indent=2))
        z.writestr(base + "connectionsMap.json", json.dumps(connections_map, indent=2))
    return out


if __name__ == "__main__":
    for folder, meta in FLOWS.items():
        print("built", build(folder, meta).relative_to(HERE.parent))
