import requests

CLUSTER_URL = "https://api.ocp800.thebrizzles.local:6443"
AUTH_TOKEN = "sha256~e5tWfEnC7aEYrAni28yTeKsSISvnE0a3eOFt40YyZls"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Accept": "application/json"
}

def get_vms():
    url = f"{CLUSTER_URL}/apis/kubevirt.io/v1/virtualmachines"
    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, headers=HEADERS, verify=False)
    response.raise_for_status()
    data = response.json()

    vms = []
    for vm in data.get("items", []):
        vms.append({
            "name": vm["metadata"]["name"],
            "namespace": vm["metadata"]["namespace"],
            "status": vm["status"].get("printableStatus", "Unknown"),
            "ready": vm["status"].get("ready", False),
            "runStrategy": vm["spec"].get("runStrategy", "Unknown"),
        })
    return vms

if __name__ == "__main__":
    for vm in get_vms():
        print(vm)