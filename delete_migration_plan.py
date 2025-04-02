import requests

def delete_migration_plan(cluster_url,auth_token,namespace,plan):

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

cluster_url = "https://api.ocp4.thebrizzles.local:6443"
namespace = "openshift-mtv"
plan = "cae-test-12"
auth_token = "sha256~MusZjo5hhm1Ny4DcnC5f6BKgENBdEyKNMZ5wjVE39Dk"
 
delete_migration_plan(cluster_url,auth_token,namespace,plan)
