import requests, json

def get_migration_plan(cluster_api_url,auth_token,namespace,plan_name):
    
    url = f"{cluster_api_url}//apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan_name}"

    # Set up headers with the Bearer auth_token for authorization
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.get(url, headers=headers, verify=False)
    api_call = response.json()
    
    if response.status_code == 200:
        print(response.json())  # Successful response
    else:
        print(f"Error: {response.status_code} - {response.text}")


# Usage:
cluster_api_url = "https://api.ocp4.example:6443"
auth_token = "" # Use your bearer auth_token
namespace = ""
plan_name = ""

get_migration_plan(cluster_api_url,auth_token,namespace,plan_name)



