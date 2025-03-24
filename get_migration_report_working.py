import requests
import json
from datetime import datetime

def get_migration_plan_details(cluster_api_url, auth_token, namespace, plan_name):
    """Fetch a migration plan from OpenShift Forklift API and extract its details."""
    url = f"{cluster_api_url}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans/{plan_name}"

    # Set up headers with the Bearer auth_token for authorization
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }

    # Suppress SSL warnings (only use in non-production environments) 
    requests.packages.urllib3.disable_warnings() # Remove for legitimate SSL Certificates

    response = requests.get(url, headers=headers, verify=False) # verify=False can be removed for legitimate SSL Certificates
    
    if response.status_code != 200:
        return {"error": f"Failed to fetch migration plan: {response.status_code} - {response.text}"}

    plan = response.json()

    # Extract plan details
    name = plan["metadata"]["name"]
    target_namespace = plan["spec"].get("targetNamespace", "N/A")

    # Extract status conditions
    conditions = plan.get("status", {}).get("conditions", [])
    migration_history = plan.get("status", {}).get("migration", {}).get("history", [])

    # Default values
    status = "Unknown"
    start_time = plan.get("status", {}).get("migration", {}).get("started")
    end_time = plan.get("status", {}).get("migration", {}).get("completed")
    error_message = "N/A"

    # Get the most recent migration status from history if available
    if migration_history:
        last_history = migration_history[-1]  # Get the most recent history entry
        for condition in last_history.get("conditions", []):
            if condition.get("type") in ["Succeeded", "Failed"]:
                status = condition.get("type")

    # If no status found in history, check top-level conditions
    if status == "Unknown":
        for condition in conditions:
            if condition.get("type") in ["Succeeded", "Failed"]:
                status = condition.get("type")

    # Extract VM names
    vms = [vm.get("name", "Unknown VM") for vm in plan.get("spec", {}).get("vms", [])]

    # Extract failure reason if migration failed
    if status == "Failed":
        for vm in plan.get("status", {}).get("migration", {}).get("vms", []):
            if "error" in vm:
                error_message = vm["error"].get("reasons", ["Unknown error"])[0]
                break  # Capture only the first failure reason

    # Calculate duration if both timestamps exist
    duration = None
    if start_time and end_time:
        start_dt = datetime.fromisoformat(start_time.rstrip("Z"))
        end_dt = datetime.fromisoformat(end_time.rstrip("Z"))
        duration = str(end_dt - start_dt)

    return {
        "plan_name": name,
        "status": status,
        "start_time": start_time or "N/A",
        "end_time": end_time or "N/A",
        "duration": duration or "N/A",
        "target_namespace": target_namespace,
        "virtual_machines": vms,
        "error_message": error_message
    }

# Usage
cluster_api_url = "https://api.ocp4.example.com:6443"
auth_token = ""  # Use your Bearer token
namespace = ""
plan_name = ""

# Fetch and extract migration plan details in one call
plan_details = get_migration_plan_details(cluster_api_url, auth_token, namespace, plan_name)

# Print the result
print(json.dumps(plan_details, indent=2))
