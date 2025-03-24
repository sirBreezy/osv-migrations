import requests, json

def get_migration_plan(cluster_api_url, auth_token, namespace, plan_name):
    
    url = f"{cluster_api_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan_name}"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    # Suppress SSL warnings (only use in non-production environments)
    requests.packages.urllib3.disable_warnings()

    response = requests.get(url, headers=headers, verify=False)
    api_call = response.json()

    try:
        with open(filename, 'w') as json_file:
            json.dump(api_call, json_file, indent=2)
        print(f'Reponse successfully written to {filename}')
    except Exception as e:
        print(f'An error occurred: {e}')

# Usage:
cluster_api_url = "https://api.ocp4.example.com:6443"
auth_token = "" # Use your bearer auth_token
namespace = ""
plan_name = ""
filename = f"{plan_name}"

get_migration_plan(cluster_api_url,auth_token,namespace,plan_name)



