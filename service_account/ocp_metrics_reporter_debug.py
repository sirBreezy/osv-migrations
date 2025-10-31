import os
import requests
import json
import urllib3
import sys
from urllib.parse import quote_plus

# Disable InsecureRequestWarning for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# Set these as environment variables.
# export OCP_API_TOKEN="<your_api_token>"
# export OCP_API_SERVER="https://api.ocp800.thebrizzles.local:6443"
# export OCP_NAMESPACE="dev-cae-team"

OCP_API_TOKEN = os.getenv('OCP_API_TOKEN')
OCP_API_SERVER = os.getenv('OCP_API_SERVER')
OCP_NAMESPACE = os.getenv('OCP_NAMESPACE', 'dev-cae-team')
VMI_NAME = 'rhel-9-osv2'

def check_vmi_status(api_server, api_token, namespace, vmi_name):
    """
    Checks if a given VMI exists and is in a 'Running' phase.
    Returns True if running, False otherwise.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    try:
        print(f"Checking status for VMI '{vmi_name}' in namespace '{namespace}'...")
        # Correct API endpoint for a VMI resource
        response = requests.get(
            f"{api_server}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachineinstances/{vmi_name}",
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

def url_encode_query(query_string):
    """
    Manually URL-encodes a Prometheus query string.
    """
    return quote_plus(query_string)

def get_prometheus_route_url(api_server, api_token):
    """
    Fetches the URL of the Prometheus route.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }
    
    # API endpoint to list routes in the openshift-monitoring namespace
    routes_url = f"{api_server}/apis/route.openshift.io/v1/namespaces/openshift-monitoring/routes/prometheus-k8s"

    try:
        response = requests.get(
            routes_url,
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        route_data = response.json()
        
        # Extract the host and build the full URL
        host = route_data['spec']['host']
        return f"https://{host}"
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Prometheus route: {e}")
        return None

def fetch_metrics_for_vmi(api_token, namespace, vmi_name):
    """
    Fetches CPU usage metrics for a specific VMI.
    """
    # First, get the Prometheus route URL
    prometheus_url = get_prometheus_route_url(OCP_API_SERVER, api_token)
    if not prometheus_url:
        print("Aborting metrics fetch due to missing Prometheus route URL.")
        return

    # Build the PromQL query string
    promql_query = f'rate(kubevirt_vmi_cpu_usage_seconds_total{{name="{vmi_name}", namespace="{namespace}"}}[5m])'
    
    # The new metrics URL uses the public route
    metrics_url = f'{prometheus_url}/api/v1/query'

    headers = {
        'Authorization': f'Bearer {api_token}'
    }
    
    query_params = {
        'query': promql_query
    }
    

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
        elif response.status_code == 404:
            print("This is a '404 Not Found' error from the API server.")
        else:
            print(f"An HTTP error occurred with status code: {response.status_code}")
        print(f"The URL requested was: {response.url}")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    if not all([OCP_API_SERVER, OCP_API_TOKEN, OCP_NAMESPACE]):
        print("Error: Please set OCP_API_SERVER, OCP_API_TOKEN, and OCP_NAMESPACE environment variables.")
        sys.exit(1)
        
    api_token = OCP_API_TOKEN
    if api_token:
        # First, check if the VMI is running before attempting to fetch metrics.
        if check_vmi_status(OCP_API_SERVER, api_token, OCP_NAMESPACE, VMI_NAME):
            fetch_metrics_for_vmi(api_token, OCP_NAMESPACE, VMI_NAME)
        else:
            print("Aborting metrics fetch.")
    else:
        print("Aborting due to token not provided. Please set the OCP_API_TOKEN environment variable.")
