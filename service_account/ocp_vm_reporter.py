import os
import requests
import json

# For development/testing, you might need to disable SSL verification.
# It is highly recommended to configure proper SSL verification in production.
VERIFY_SSL = False

def get_vms(api_server, api_token, namespace):
    """
    Fetches a list of VirtualMachineInstances in a given namespace.
    """
    vm_api_url = f"{api_server}/apis/kubevirt.io/v1/namespaces/{namespace}/virtualmachineinstances"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(vm_api_url, headers=headers, verify=VERIFY_SSL)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching VMs: {e}")
        return None

def check_vmi_status(api_server, api_token, namespace, vmi_name):
    """
    Checks if a given VMI exists and is in a 'Running' phase.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            f"{api_server}/apis/subresources.kubevirt.io/v1/namespaces/{namespace}/virtualmachineinstances/{vmi_name}/status",
            headers=headers,
            verify=False
        )
        response.raise_for_status()
        vmi_status = response.json()
        if vmi_status.get('status', {}).get('phase') == 'Running':
            return True
        else:
            print(f"VMI '{vmi_name}' is not in a 'Running' phase. Current phase: {vmi_status.get('status', {}).get('phase')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error checking VMI status: {e}")
        return False
    
def fetch_metrics(api_server, api_token, namespace, vmi_name):
    query_params = {
        'query': f'rate(kubevirt_vmi_cpu_usage_seconds_total{{name="{vmi_name}", namespace="{namespace}"}}[5m])'
    }

    headers = {
        'Authorization': f'Bearer {api_token}'
    }

    metrics_url = f'{api_server}/api/v1/query'

    # --- ADD THESE LINES FOR DEBUGGING ---
    print("\n--- DEBUGGING METRICS REQUEST ---")
    print(f"Request URL: {metrics_url}")
    print(f"Query Parameters: {query_params}")
    print(f"Headers: {headers}")
    print("-----------------------------------")
    # ------------------------------------

    try:
        response = requests.get(
            metrics_url,
            headers=headers,
            params=query_params,
            verify=False
        )
        response.raise_for_status()

def get_vm_metrics(api_server, api_token, namespace, vm_name):
    """
    Fetches CPU and memory metrics for a specific VM using the Prometheus-compatible API.
    Note: Assumes OpenShift's default monitoring stack is in place.
    """
    # The API path for metrics is a bit more complex, using the query endpoint
    # for a Prometheus-style query.
    metrics_api_url = f"{api_server}/api/v1/query"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }

    # Prometheus queries for CPU and memory usage of a KubeVirt VMI.
    # We use `kubevirt_vmi_cpu_usage_seconds_total` and `kubevirt_vmi_memory_bytes`
    # metrics, and filter by the VMI name and namespace.
    cpu_query = f'rate(kubevirt_vmi_cpu_usage_seconds_total{{name="{vm_name}", namespace="{namespace}"}}[5m])'
    memory_query = f'kubevirt_vmi_memory_bytes{{name="{vm_name}", namespace="{namespace}"}}'

    metrics = {}

    try:
        # Fetch CPU metrics
        cpu_params = {'query': cpu_query}
        cpu_response = requests.get(metrics_api_url, headers=headers, params=cpu_params, verify=VERIFY_SSL)
        cpu_response.raise_for_status()
        cpu_data = cpu_response.json()
        cpu_value = cpu_data.get('data', {}).get('result', [{}])[0].get('value', [1, '0'])[1]
        metrics['cpu_usage'] = float(cpu_value) * 100  # Convert to percentage

        # Fetch Memory metrics
        memory_params = {'query': memory_query}
        memory_response = requests.get(metrics_api_url, headers=headers, params=memory_params, verify=VERIFY_SSL)
        memory_response.raise_for_status()
        memory_data = memory_response.json()
        memory_value = memory_data.get('data', {}).get('result', [{}])[0].get('value', [1, '0'])[1]
        metrics['memory_bytes'] = int(memory_value)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics for {vm_name}: {e}")
    except (IndexError, TypeError, KeyError) as e:
        print(f"Error parsing metrics data for {vm_name}: {e}")

    return metrics

def main():
    """
    Main function to report on VMs and their performance.
    """
    # Load environment variables
    api_token = os.getenv('OCP_API_TOKEN')
    api_server = os.getenv('OCP_API_SERVER')
    namespace = os.getenv('OCP_NAMESPACE', 'default')

    if not all([api_token, api_server]):
        print("Error: OCP_API_TOKEN and OCP_API_SERVER must be set.")
        return

    print(f"Connecting to {api_server} to report on VMs in namespace '{namespace}'...")

    vms = get_vms(api_server, api_token, namespace)
    if vms is None:
        return

    if not vms:
        print(f"No VirtualMachineInstances found in namespace '{namespace}'.")
        return

    print("\n--- VM Performance Report ---")
    for vm in vms:
        vm_name = vm['metadata']['name']
        vm_status = vm.get('status', {}).get('phase', 'Unknown')
        
        # Only fetch metrics for running VMs
        metrics = {}
        #if vm_status == 'Running':
        #    metrics = get_vm_metrics(api_server, api_token, namespace, vm_name)
        
        print(f"VM Name: {vm_name}")
        print(f"  Status: {vm_status}")
        if metrics:
            cpu_percent = metrics.get('cpu_usage', 0)
            memory_bytes = metrics.get('memory_bytes', 0)
            memory_mb = memory_bytes / (1024 * 1024)
            print(f"  CPU Usage: {cpu_percent:.2f}%")
            print(f"  Memory Usage: {memory_mb:.2f} MB")
        print("-" * 25)

        if check_vmi_status(api_server, api_token, namespace, 'rhel-9-osv2'):
            fetch_metrics()

if __name__ == "__main__":
    main()
