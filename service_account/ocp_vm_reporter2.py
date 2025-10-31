import os
import requests
import json
import urllib3

# Disable InsecureRequestWarning for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# It's best practice to set these as environment variables.
# For example:
OCP_CLUSTER_URL="https://api.ocp800.thebrizzles.local:6443"
OCP_AUTH_TOKEN="sha256~jrbyXOiWcQHiONQTPDk7GkIdAHiSrFoxSOwplcnkaGI"
OCP_NAMESPACE="cae-vms"

#OCP_AUTH_TOKEN = os.getenv('OCP_AUTH_TOKEN')
#OCP_CLUSTER_URL = os.getenv('OCP_CLUSTER_URL')
#OCP_NAMESPACE = os.getenv('OCP_NAMESPACE', 'cae-vms')

def check_vmi_status(cluster_url, auth_token, namespace, vmi_name):
    """
    Checks if a given VMI exists and is in a 'Running' phase.
    Returns True if running, False otherwise.
    """
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }

    try:
        print(f"Checking status for VMI '{vmi_name}' in namespace '{namespace}'...")
        # Correct API endpoint for a VMI resource
        response = requests.get(
            f"{cluster_url}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachineinstances/{vmi_name}",
            headers=headers,
            verify=False
        )

        if response.status_code == 404:
            print(f"VMI '{vmi_name}' not found in namespace '{namespace}'.")
            return False

        response.raise_for_status()
        vmi_status = response.json()
        
        phase = vmi_status.get('status', {}).get('phase')
        if phase == 'Running':
            print(f"VMI '{vmi_name}' is in 'Running' phase.")
            return True
        else:
            print(f"VMI '{vmi_name}' is not running. Current phase: {phase}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error checking VMI status: {e}")
        return False

def fetch_metrics_for_vmi(cluster_url, auth_token, namespace, vmi_name):
    """
    Fetches CPU usage metrics for a specific VMI.
    Includes debug output to help diagnose 404 errors.
    """
    query_params = {
        'query': f'rate(kubevirt_vmi_cpu_usage_seconds_total{{name="{vmi_name}", namespace="{namespace}"}}[5m])'
    }

    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    
    # CORRECTED URL: Use the proxy endpoint to the Prometheus service
    # NOTE: Your service account needs the 'cluster-monitoring-view' role
    # to access this API endpoint.
    metrics_url = f'{cluster_url}/api/v1/namespaces/openshift-monitoring/services/https:prometheus-k8s:9091/proxy/api/v1/query'

    # --- DEBUGGING OUTPUT ---
    print("\n--- DEBUGGING METRICS REQUEST ---")
    print(f"Request URL: {metrics_url}")
    print(f"Query Parameters: {json.dumps(query_params, indent=2)}")
    print(f"Headers: {headers}")
    print("-----------------------------------\n")

    try:
        response = requests.get(
            metrics_url,
            headers=headers,
            params=query_params,
            verify=False
        )
        
        response.raise_for_status()
        metrics_data = response.json()
        
        # Process and print the metrics
        if metrics_data['data']['result']:
            metric = metrics_data['data']['result'][0]
            print(f"Successfully fetched metrics for '{vmi_name}':")
            print(f"  CPU usage rate (over 5m): {metric['value'][1]}")
        else:
            print(f"Metrics data not found for '{vmi_name}'. The VMI may not have metrics available yet.")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching metrics: {e}")
        if response.status_code == 403:
            print("This is a '403 Forbidden' error. The service account lacks the necessary permissions to access the metrics API.")
            print("Please ensure your service account has the 'cluster-monitoring-view' role.")
        elif response.status_code == 404:
            print("This is a '404 Not Found' error from the API server.")
            print("Please check that the VMI exists and is actively collecting metrics.")
        else:
            print(f"An HTTP error occurred with status code: {response.status_code}")
        print(f"The URL requested was: {response.url}")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred: {e}")

def get_sa_token(cluster_url, auth_token, namespace, sa_name):
    """
    A helper function to demonstrate how to get the latest service account token.
    This is not a general-purpose function and should be run manually.
    """
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json"
    }
    try:
        sa_response = requests.get(
            f"{cluster_url}/api/v1/namespaces/{namespace}/serviceaccounts/{sa_name}",
            headers=headers,
            verify=False
        )
        sa_response.raise_for_status()
        sa_data = sa_response.json()
        secret_name = sa_data['secrets'][0]['name']

        secret_response = requests.get(
            f"{cluster_url}/api/v1/namespaces/{namespace}/secrets/{secret_name}",
            headers=headers,
            verify=False
        )
        secret_response.raise_for_status()
        secret_data = secret_response.json()
        
        new_token = secret_data['data']['token']
        print("\n--- NEW SERVICE ACCOUNT TOKEN ---")
        print("Please copy the token below and use it to update your OCP_auth_token environment variable.")
        print(f"New Token: {new_token}")
        print("---------------------------------")
    except Exception as e:
        print(f"Error fetching new token: {e}")

if __name__ == "__main__":
    if not all([OCP_AUTH_TOKEN, OCP_CLUSTER_URL, OCP_NAMESPACE]):
        print("Error: Please set OCP_AUTH_TOKEN, OCP_CLUSTER_URL, and OCP_NAMESPACE environment variables.")
    else:
        vmi_to_check = 'rhel9-vmware'
        
        # This function call is for manual use to get a new token
        # get_sa_token(OCP_CLUSTER_URL, OCP_auth_token, OCP_NAMESPACE, 'dev-sa')

        # First, check if the VMI is running before attempting to fetch metrics.
        if check_vmi_status(OCP_CLUSTER_URL, OCP_AUTH_TOKEN, OCP_NAMESPACE, vmi_to_check):
            fetch_metrics_for_vmi(OCP_CLUSTER_URL, OCP_AUTH_TOKEN, OCP_NAMESPACE, vmi_to_check)
        else:
            print("Aborting metrics fetch. Please ensure the VMI is running and the name/namespace are correct.")
