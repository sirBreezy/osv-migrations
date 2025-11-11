import requests

def list_migration_plans(cluster_url, namespace, auth_token):

    url = f"{cluster_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }

    # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.get(url, headers=headers, verify=False)  # verify=False can be removed for legitimate SSL Certificates

    if response.status_code == 200:
        plans = response.json().get("items", [])
        print(f"Found {len(plans)} migration plans in namespace '{namespace}':")
        for plan in plans:
            print(f"- {plan['metadata']['name']} (Status: {plan['status'].get('conditions', [{}])[-1].get('type', 'Unknown')})")
        return plans
    else:
        print(f"Failed to retrieve migration plans: {response.status_code} - {response.text}")
        return None

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
namespace = "openshift-mtv"  # Specify the namespace
auth_token = "sha256~"  # Bearer Token

list_migration_plans(cluster_url, namespace, auth_token)
