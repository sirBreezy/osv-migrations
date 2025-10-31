import json

def get_namespaces_by_annotation(json_data, annotation_key, annotation_value=None):
    """
    Extract namespaces associated with a specific annotation from the provided JSON data.
    
    Args:
        json_data (dict): The JSON data containing namespace details.
        annotation_key (str): The key of the annotation to filter namespaces by.
        annotation_value (str, optional): The value of the annotation to filter namespaces by.
            If None, any namespace with the specified annotation key will be included.
    
    Returns:
        dict: A dictionary where keys are namespace names and values are their annotations.
    """
    namespaces = {}
    
    # Iterate through the items in the JSON data
    for item in json_data.get("items", []):
        metadata = item.get("metadata", {})
        annotations = metadata.get("annotations", {})
        
        # Check if the annotation key exists and optionally if the value matches
        if annotation_key in annotations and (annotation_value is None or annotations[annotation_key] == annotation_value):
            namespaces[metadata.get("name")] = annotations
    
    return namespaces

# Load the JSON file
with open('namespaces.json', 'r') as file:
    data = json.load(file)

# Example usage
annotation_to_search = "openshift.io/sa.scc.supplemental-groups"  # Replace with the desired annotation key
annotation_value_to_search = None  # Replace with the desired annotation value or None

# Get namespaces associated with the provided annotation
namespaces = get_namespaces_by_annotation(data, annotation_to_search, annotation_value_to_search)
print("Namespaces with the specified annotation:", json.dumps(namespaces, indent=2))
