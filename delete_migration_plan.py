import requests

def delete_migration_plan(cluster_url, auth_token, namespace, plan):

    url = f"{cluster_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan}"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }

     # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.delete(url, headers=headers, verify=False) # verify=False can be removed for legitimate SSL Certificates

    if response.status_code in [200, 202, 204]:
        print(f"Migration plan '{plan}' deleted successfully.")
        return True
    else:
        print(f"Failed to delete plan '{plan}': {response.status_code} - {response.text}")
        return False

# Example usage
cluster_url = "https://api.ocp4.example.com:6443"
auth_token = ""
namespace = ""
plan = ""

 
delete_migration_plan(cluster_url , namespace, plan, auth_token)
