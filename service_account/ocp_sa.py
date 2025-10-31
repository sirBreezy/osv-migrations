import os
import requests
import sys

def main():
    """
    Connects to the OpenShift API using a Service Account token and lists pods
    using the requests library.
    """
    cluster_url="https://api.ocp800.thebrizzles.local:6443"
    auth_token="sha256~WaDdH_7OXZ6Z_h68xCISqI71uMFq3k9w_IGrVbHaPXk"
    namespace="openshift-mtv"

    requests.packages.urllib3.disable_warnings()

    # Load the API token and API server URL from environment variables
    #auth_token = os.getenv('OCP_AUTH_TOKEN')
    #cluster_url = os.getenv('OCP_CLUSTER_URL')
    #namespace = os.getenv('OCP_NAMESPACE', 'default')

    # Ensure all required environment variables are set
    if not auth_token or not cluster_url:
        print("Error: OCP_AUTH_TOKEN and OCP_CLUSTER_URL environment variables must be set.")
        print("Please set them before running the script.")
        return

    # Construct the full API URL for listing pods in the specified namespace.
    # The Kubernetes API for pods is at /api/v1/namespaces/{namespace}/pods
    url = f"{cluster_url}/api/v1/namespaces/{namespace}/pods"

    # Set up the headers for the request. The Authorization header
    # is required and uses the 'Bearer' scheme with the token.
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    # For development/testing, you might need to disable SSL verification.
    # It is highly recommended to configure proper SSL verification in production.
    verify_ssl = False

    try:
        print(f"Attempting to list pods in namespace '{namespace}' from {cluster_url}...")
        # Make the GET request to the OpenShift API
        response = requests.get(url, headers=headers, verify=verify_ssl)

        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response
        pods = response.json()

        # Check if there are any pods in the 'items' key of the response
        if pods.get('items'):
            print("Pods found:")
            for pod in pods['items']:
                name = pod['metadata']['name']
                status = pod['status']['phase']
                print(f" - Name: {name}, Status: {status}")
        else:
            print("No pods found in the specified namespace.")

    except requests.exceptions.RequestException as e:
        # This block catches all requests-related errors (network issues, bad status codes)
        print(f"An error occurred while making the API request: {e}")
        if response.status_code == 401:
            print("Authentication failed. Please check your token.")
        elif response.status_code == 403:
            print("Permission denied. The service account may not have sufficient permissions to list pods.")
        elif response.status_code == 404:
            print(f"The namespace '{namespace}' or API endpoint was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()