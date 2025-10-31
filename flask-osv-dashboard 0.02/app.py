from flask import Flask, render_template, jsonify
import requests
import time

app = Flask(__name__)

# OpenShift / KubeVirt API settings
CLUSTER_URL = "https://api.ocp800.thebrizzles.local:6443"
TOKEN = "sha256~13Le413LuGKSMZMogKYVFU95_uVXeyRLDN4UcZ34tUI"
NAMESPACE = "dev-cae-team"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# List VMs across all namespaces
@app.route("/")
def index():
    url = f"{CLUSTER_URL}/apis/kubevirt.io/v1/virtualmachines"
    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=HEADERS, verify=False)
    vms = response.json().get("items", [])
    return render_template("index.html", vms=vms)

# VM actions (start, stop, restart)
@app.route("/vm/<namespace>/<name>/<action>", methods=["POST"])
def vm_action(namespace, name, action):
    if action not in ["start", "stop", "restart"]:
        return jsonify({"error": "Invalid action"}), 400

    url = f"{OPENSHIFT_API_URL}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachines/{name}"

    # Define headers for the PATCH request
    patch_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/merge-patch+json",
        "Accept": "application/json"
    }

    if action == "start":
        data = {"spec": {"runStrategy": "Always"}}
        response = requests.patch(url, headers=patch_headers, json=data, verify=False)
    elif action == "stop":
        data = {"spec": {"runStrategy": "Halted"}}
        response = requests.patch(url, headers=patch_headers, json=data, verify=False)
    elif action == "restart":
        # First, set to Halted
        response = requests.patch(url, headers=patch_headers, json={"spec": {"runStrategy": "Halted"}}, verify=False)
        
        # Add a delay to allow the VM to shut down
        if response.status_code in [200, 201, 202]:
            time.sleep(5)
            # Then, set to Always to start it again
            data = {"spec": {"runStrategy": "Always"}}
            response = requests.patch(url, headers=patch_headers, json=data, verify=False)
        else:
            return jsonify({"status": "failed", "details": response.text})

    if response.status_code in [200, 201, 202]:
        return jsonify({"status": "success"})
    return jsonify({"status": "failed", "details": response.text})

@app.route("/api/vms")
def api_vms():
    url = f"{CLUSTER_URL}/apis/kubevirt.io/v1/virtualmachines"
    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=HEADERS, verify=False)
    vms = response.json().get("items", [])

    result = []
    for vm in vms:
        spec = vm.get("spec", {})
        status = vm.get("status", {})

        # Snapshots
        snapshots = []
        for snap in status.get("volumeSnapshotStatuses", []):
            if snap.get("enabled"):
                snapshots.append(f"✅ {snap['name']}")
            else:
                snapshots.append(f"❌ {snap['name']} ({snap.get('reason','')})")

        # Warnings
        warnings = []
        for cond in status.get("conditions", []):
            if cond.get("status") == "False":
                warnings.append(f"{cond['type']}: {cond.get('message','')}")

        # Storage info
        storage = "-"
        if vm.get("spec", {}).get("dataVolumeTemplates"):
            for dv in vm["spec"]["dataVolumeTemplates"]:
                size = dv.get("spec", {}).get("storage", {}).get("resources", {}).get("requests", {}).get("storage", "-")
                sc = dv.get("spec", {}).get("storage", {}).get("storageClassName", "default")
                storage = f"{size} ({sc})"


        # Network
        mac = "-"
        if spec.get("template", {}).get("spec", {}).get("domain", {}).get("devices", {}).get("interfaces"):
            mac = spec["template"]["spec"]["domain"]["devices"]["interfaces"][0].get("macAddress", "-")

        result.append({
            "name": vm["metadata"]["name"],
            "namespace": vm["metadata"]["namespace"],
            "status": status.get("printableStatus", "Unknown"),
            "ready": status.get("ready", False),
            "runStrategy": spec.get("runStrategy", "-"),
            "type": spec.get("instancetype", {}).get("name", "-"),
            "preference": spec.get("preference", {}).get("name", "-"),
            "storage": storage,
            "mac": mac,
            "created": vm["metadata"]["creationTimestamp"],
            "snapshots": "<br>".join(snapshots) if snapshots else "-",
            "warnings": "<br>".join(warnings) if warnings else "-"
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
