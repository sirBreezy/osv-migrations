from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# OpenShift / KubeVirt API settings
OPENSHIFT_API_URL = "https://api.ocp800.thebrizzles.local:6443"
TOKEN = "sha256~JQ6L_eGCHzkisaatko9UeOI14TXZ-cixVTnV-A7R9Ik"
NAMESPACE = "dev-cae-team"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# List VMs across all namespaces
@app.route("/")
def index():
    url = f"{OPENSHIFT_API_URL}/apis/kubevirt.io/v1/virtualmachines"
    response = requests.get(url, headers=HEADERS, verify=False)
    vms = response.json().get("items", [])
    return render_template("index.html", vms=vms)

# VM actions (start, stop, restart)
@app.route("/vm/<namespace>/<name>/<action>", methods=["POST"])
def vm_action(namespace, name, action):
    if action not in ["start", "stop", "restart"]:
        return jsonify({"error": "Invalid action"}), 400

    url = f"{OPENSHIFT_API_URL}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachines/{name}"

    if action == "start":
        data = {"spec": {"runStrategy": "Always"}}
    elif action == "stop":
        data = {"spec": {"runStrategy": "Halted"}}
    elif action == "restart":
        # Restart = set Halted then Always again
        requests.patch(url, headers=HEADERS, json={"spec": {"runStrategy": "Halted"}}, verify=False)
        data = {"spec": {"runStrategy": "Always"}}

    response = requests.patch(url, headers=HEADERS, json=data, verify=False)
    if response.status_code in [200, 201]:
        return jsonify({"status": "success"})
    return jsonify({"status": "failed", "details": response.text})

if __name__ == "__main__":
    app.run(debug=True)
