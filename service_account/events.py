import os
import requests
import sys
import json

def main():
    """
    Connects to the OpenShift API using a Service Account token and watches for events
    using the requests library.
    """
    # Load the API token and API server URL from environment variables
    api_token = os.getenv('OCP_API_TOKEN')
    api_server = os.getenv('OCP_API_SERVER')
    namespace = os.getenv('OCP_NAMESPACE', 'default')

    # Ensure all required environment variables are set
    if not api_token or not api_server:
        print("Error: OCP_API_TOKEN and OCP_API_SERVER environment variables must be set.")
        print("Please set them before running the script.")
        return

    # Construct the API URL for watching events.
    # The 'watch' endpoint for events is at /api/v1/watch/namespaces/{namespace}/events
    api_url = f"{api_server}/api/v1/watch/namespaces/{namespace}/events"

    # Set up the headers for the request. The Authorization header
    # is required and uses the 'Bearer' scheme with the token.
    headers = {
        "Authorization": f"Bearer {api_token}",
        # The 'Accept' header specifies we're expecting JSON data.
        "Accept": "application/json"
    }

    # For development/testing, you might need to disable SSL verification.
    # It is highly recommended to configure proper SSL verification in production.
    verify_ssl = False

    try:
        print(f"Watching for events in namespace '{namespace}' from {api_server}...")
        # Use a streaming GET request to keep the connection open and process events as they arrive.
        # The 'stream=True' parameter is crucial for this.
        with requests.get(api_url, headers=headers, verify=verify_ssl, stream=True) as response:
            # Raise an HTTPError for bad responses (4xx or 5xx)
            response.raise_for_status()

            # Iterate over the response content line by line.
            for line in response.iter_lines():
                if line:
                    try:
                        # Decode the JSON object from the line.
                        event_data = json.loads(line)
                        
                        # Extract and print key information about the event.
                        event_type = event_data.get('type')
                        event_object = event_data.get('object', {})
                        reason = event_object.get('reason')
                        message = event_object.get('message')
                        involved_object = event_object.get('involvedObject', {})
                        involved_object_kind = involved_object.get('kind')
                        involved_object_name = involved_object.get('name')

                        print("---")
                        print(f"Event Type: {event_type}")
                        print(f"Reason: {reason}")
                        print(f"Message: {message}")
                        print(f"Involved Object: {involved_object_kind}/{involved_object_name}")
                        print("---")

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from a response line: {e}")
                        print(f"Line content: {line.decode('utf-8')}")

    except requests.exceptions.RequestException as e:
        # This block catches all requests-related errors (network issues, bad status codes)
        print(f"An error occurred while making the API request: {e}")
        # Add specific error messages for common HTTP status codes
        if response.status_code == 401:
            print("Authentication failed. Please check your token.")
        elif response.status_code == 403:
            print("Permission denied. The service account may not have sufficient permissions to watch events.")
        elif response.status_code == 404:
            print(f"The namespace '{namespace}' or API endpoint was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()