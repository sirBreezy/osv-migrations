import os
import requests
import json

# For development/testing, you might need to disable SSL verification.
# It is highly recommended to configure proper SSL verification in production.
VERIFY_SSL = False

def create_role_and_role_binding(api_server, api_token, namespace, service_account_name):
    """
    Creates a Role and RoleBinding to grant a service account read-only access
    to the Prometheus metrics API in a specific namespace.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Define the Role object. This role grants 'get' and 'list' verbs on the
    # 'prometheusrules' resource in the 'monitoring.coreos.com' API group.
    # It also includes rules to allow querying the metrics API.
    role_name = f"{service_account_name}-metrics-reader"
    role_payload = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": {
            "name": role_name,
            "namespace": namespace
        },
        "rules": [
            {
                "apiGroups": ["monitoring.coreos.com"],
                "resources": ["prometheusrules"],
                "verbs": ["get", "list"]
            },
            {
                "nonResourceURLs": ["/api/v1/query", "/api/v1/query_range"],
                "verbs": ["get", "list"]
            },
            {
                "apiGroups": ["metrics.k8s.io"],
                "resources": ["*"],
                "verbs": ["get", "list"]
            }
        ]
    }
    
    # Define the RoleBinding object to bind the new role to the service account.
    role_binding_payload = {
        "apiVersion": "rbac.authorization.k8s.sio/v1",
        "kind": "RoleBinding",
        "metadata": {
            "name": f"{service_account_name}-metrics-binding",
            "namespace": namespace
        },
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "Role",
            "name": role_name
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": service_account_name,
                "namespace": namespace
            }
        ]
    }

    try:
        # Create the Role
        print(f"Creating Role '{role_name}'...")
        response = requests.post(
            f"{api_server}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/roles",
            headers=headers,
            data=json.dumps(role_payload),
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        print(f"Successfully created Role '{role_name}'.")

        # Create the RoleBinding
        print(f"Creating RoleBinding for service account '{service_account_name}'...")
        response = requests.post(
            f"{api_server}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings",
            headers=headers,
            data=json.dumps(role_binding_payload),
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        print(f"Successfully created RoleBinding for '{service_account_name}'.")

    except requests.exceptions.RequestException as e:
        print(f"Error creating RBAC resources: {e}")
        print("Please check your token and permissions.")
        return False
    
    return True

def main():
    """
    Main function to create necessary RBAC permissions for a service account.
    """
    # Load environment variables
    api_token = os.getenv('OCP_API_TOKEN')
    api_server = os.getenv('OCP_API_SERVER')
    namespace = os.getenv('OCP_NAMESPACE')
    service_account_name = os.getenv('OCP_SA_NAME')

    if not all([api_token, api_server, namespace, service_account_name]):
        print("Error: OCP_API_TOKEN, OCP_API_SERVER, OCP_NAMESPACE, and OCP_SA_NAME must be set.")
        return

    print(f"Attempting to grant permissions to '{service_account_name}' in namespace '{namespace}'...")

    if create_role_and_role_binding(api_server, api_token, namespace, service_account_name):
        print("\nRBAC resources created successfully.")
        print("You can now re-run the 'ocp_vm_reporter.py' script.")
    else:
        print("\nFailed to create RBAC resources. Please review the error messages above.")

if __name__ == "__main__":
    main()
