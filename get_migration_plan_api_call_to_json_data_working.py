import requests, json

def get_migration_plan(cluster_url,auth_token,namespace,plan):
    
    url = f"{cluster_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan}"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.get(url, headers=headers, verify=False) # remove verify=false for signed ssl
    payload = response.json()
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")

    print(payload) 
    
        
# Usage:
cluster_url = "https://api.ocp4.example:6443"
auth_token = "" # Use your bearer auth_token
namespace = ""
plan = ""

get_migration_plan(cluster_url,auth_token,namespace,plan)



