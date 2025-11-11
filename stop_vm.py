import requests, json

def stop_vm(cluster_url, namespace, vm_name, auth_token):

    url = f"{cluster_url}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachines/{vm_name}"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/merge-patch+json"
    }

    payload = {"spec": {"running": False}}  # Instead of using /start, modify the VM spec

    requests.packages.urllib3.disable_warnings()

    response = requests.patch(url, headers=headers, json=payload, verify=False)

    if response.status_code in [200, 202]:
        print(f"VM '{vm_name}' stopped successfully.")
        return True
    else:
        print(f"Failed to stop VM '{vm_name}': {response.status_code} - {response.text}")
        return False

def stop_multiple_vms(cluster_url, namespace, vm_names, auth_token):
    for vm_name in vm_names:
        success = stop_vm(cluster_url, namespace, vm_name, auth_token)
        if success:
            print(f"✅ VM '{vm_name}' stopped successfully.")
        else:
            print(f"❌ Failed to stop VM '{vm_name}'.")

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
namespace = ""  
auth_token = ""
#vm_name = "rhel9-vm"

vm_list = ["fedora-vm", "rhel9-vm"]  # Replace with actual VM names

#stop_vm(cluster_url, namespace, vm_name, auth_token)
stop_multiple_vms(cluster_url, namespace, vm_list, auth_token)
