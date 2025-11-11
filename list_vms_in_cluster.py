import requests

def list_vms_in_cluster(cluster_url, auth_token):
    url = f"{cluster_url}/apis/kubevirt.io/v1/virtualmachines"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }

    requests.packages.urllib3.disable_warnings()

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        vms = response.json().get("items", [])
        print(f"Found {len(vms)} VMs:")
        for vm in vms:
            vm_name = vm["metadata"]["name"]
            status = vm.get("status", {}).get("printableStatus", "Unknown")
            print(f"- {vm_name} (Status: {status})")
        return vms
    else:
        print(f"Failed to list VMs: {response.status_code} - {response.text}")
        return None

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
auth_token = ""  # Bearer Token

list_vms_in_cluster(cluster_url, auth_token)
