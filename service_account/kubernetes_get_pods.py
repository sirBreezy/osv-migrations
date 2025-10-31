import os
import sys
import urllib3

# Disable InsecureRequestWarning for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from kubernetes.client import Configuration, ApiClient, CoreV1Api, rest
except ImportError as e:
    print("Error: The kubernetes Python client library is not installed or cannot be found.")
    print("Please ensure you are running this script with the same Python interpreter used for 'pip install kubernetes'.")
    print(f"Details: {e}")
    # Optional: Check for the package path to help with diagnosis
    if "/.local/" in str(sys.path):
        print("\nNote: The '.local' directory is in your Python path, so the package *should* be accessible.")
    exit()

def main():
    """
    Connects to the OpenShift API using a Service Account token and lists pods.
    """
    # Load the API token and API server URL from environment variables
    # It is best practice to not hardcode these values in your script.
    api_token = os.getenv('OCP_API_TOKEN')
    api_server = os.getenv('OCP_API_SERVER')
    namespace = os.getenv('OCP_NAMESPACE', 'default') # Use 'default' if not specified

    # Ensure all required environment variables are set
    if not api_token or not api_server:
        print("Error: OCP_API_TOKEN and OCP_API_SERVER environment variables must be set.")
        return

    # Configuration for using the token
    configuration = Configuration()
    configuration.host = api_server
    
    # Add the Bearer token for authentication
    configuration.api_key = {'authorization': 'Bearer ' + api_token}
    
    # Depending on your cluster's CA certificate, you may need to disable SSL verification.
    # For production environments, it is highly recommended to configure proper SSL verification.
    configuration.verify_ssl = False 

    # Create a client instance
    api_client = ApiClient(configuration)

    # Initialize the CoreV1Api to interact with pod resources
    v1 = CoreV1Api(api_client)

    try:
        print(f"Listing pods in namespace '{namespace}'...")
        # List the pods in the specified namespace
        pods = v1.list_namespaced_pod(namespace=namespace)

        # Check if there are any pods
        if pods.items:
            for pod in pods.items:
                print(f"Pod Name: {pod.metadata.name}, Status: {pod.status.phase}")
        else:
            print("No pods found.")

    except rest.ApiException as e:
        print(f"Error accessing the API: {e}")
        print("Please check your token and permissions.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()