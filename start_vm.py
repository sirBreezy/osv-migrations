import requests, json

def start_vm(cluster_url, namespace, vm_name, auth_token):
    url = f"{cluster_url}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachines/{vm_name}"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/merge-patch+json"
    }

    payload = {"spec": {"running": True}}  # Instead of using /start, modify the VM spec

    requests.packages.urllib3.disable_warnings()

    response = requests.patch(url, headers=headers, json=payload, verify=False)

    if response.status_code in [200, 202]:
        print(f"VM '{vm_name}' started successfully.")
        return True
    else:
        print(f"Failed to start VM '{vm_name}': {response.status_code} - {response.text}")
        return False

def start_multiple_vms(cluster_url, namespace, vm_names, auth_token):
    for vm_name in vm_names:
        success = start_vm(cluster_url, namespace, vm_name, auth_token)
        if success:
            print(f"✅ VM '{vm_name}' started successfully.")
        else:
            print(f"❌ Failed to start VM '{vm_name}'.")

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
namespace = ""  
auth_token = ""
vm_name = "fedora-vm"
vm_list = ["fedora-vm", "rhel9-vm"]


start_multiple_vms(cluster_url, namespace, vm_list, auth_token)

# start_vm(cluster_url, namespace, vm_name, auth_token)
