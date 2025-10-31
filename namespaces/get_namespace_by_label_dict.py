import json

def get_namespaces_by_label(json_data, label_key, label_value=None):
    """
    Extract namespaces associated with a specific label from the provided JSON data.
    
    Args:
        json_data (dict): The JSON data containing namespace details.
        label_key (str): The key of the label to filter namespaces by.
        label_value (str, optional): The value of the label to filter namespaces by.
            If None, any namespace with the specified label key will be included.
    
    Returns:
        dict: A dictionary where keys are namespace names and values are their labels.
    """
    namespaces = {}
    
    # Iterate through the items in the JSON data
    for item in json_data.get("items", []):
        metadata = item.get("metadata", {})
        labels = metadata.get("labels", {})
        
        # Check if the label key exists and optionally if the value matches
        if label_key in labels and (label_value is None or labels[label_key] == label_value):
            namespaces[metadata.get("name")] = labels
    
    return namespaces

# Load the JSON file
with open('namespaces.json', 'r') as file:
    data = json.load(file)

# Example usage
label_to_search = "openshift-pipelines.tekton.dev/namespace-reconcile-version"  # Replace with the desired label key
label_value_to_search = None  # Replace with the desired label value or None

# Get namespaces associated with the provided label
namespaces = get_namespaces_by_label(data, label_to_search, label_value_to_search)
print("Namespaces with the specified label:", json.dumps(namespaces, indent=2))
