import requests

def archive_migration_plan(cluster_url,auth_token,namespace,plan):
    url = f"{cluster_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan}"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/merge-patch+json"
    }

    payload = {"spec": {"archived": True}}

    # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.patch(url, headers=headers, json=payload, verify=False)  # verify=False can be removed for legitimate SSL Certificates

    if response.status_code in [200, 202]:
        print(f"Migration plan '{plan}' archived successfully.")
        return True
    else:
        print(f"Failed to patch plan '{plan}': {response.status_code} - {response.text}")
        return False

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
namespace = ""
plan = ""
auth_token = ""

archive_migration_plan(cluster_url,auth_token,namespace,plan)
