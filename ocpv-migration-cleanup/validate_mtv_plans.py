import os,json,requests,sys

def get_ocp_api_info():
    """Retrieves in-cluster Kubernetes API information."""
    #host = "https://kubernetes.default.svc"
    host = "https://api.ocp800.thebrizzles.local:6443"
    #token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    #ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    token="sha256~jrbyXOiWcQHiONQTPDk7GkIdAHiSrFoxSOwplcnkaGI"
    namespace="openshift-mtv"
    #if not os.path.exists(token_path):
    #    raise FileNotFoundError("Service account token not found.")
    #
    #with open(token_path, "r") as f:
    #    token = f.read().strip()

    #return host, token, ca_cert_path
    return host, token, namespace

# def get_mtv_plans(host, token, ca_cert, namespace):
def get_mtv_plans(host, token, namespace):
    """Fetches all MTV Plan custom resources using the Kubernetes API."""
    url = f"{host}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    print(f"Fetching MTV plans from {url}")
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    
    return response.json()

def validate_plans(plans):
    """
    Validates that each VM is in only one migration plan.
    Prints an error and exits if a duplicate is found.
    """
    if not plans.get("items"):
        print("No MTV plans found. Validation successful.")
        return

    vm_plan_map = {}
    
    for plan in plans["items"]:
        plan_name = plan["metadata"]["name"]
        
        for vm in plan.get("spec", {}).get("vms", []):
            vm_name = vm.get("name")
            if not vm_name:
                continue
            
            if vm_name in vm_plan_map:
                existing_plans = vm_plan_map[vm_name]
                if plan_name not in existing_plans:
                    existing_plans.append(plan_name)
                
            else:
                vm_plan_map[vm_name] = [plan_name]

    duplicate_found = False
    for vm_name, plan_list in vm_plan_map.items():
        if len(plan_list) > 1:
            print(f"ERROR: VM '{vm_name}' is in multiple plans: \n{', '.join(plan_list)}")
            duplicate_found = True
    
    if duplicate_found:
        print("Validation failed: Duplicate VMs found across multiple plans.")
        exit(1)
    else:
        print("Validation successful: No VMs are found in multiple plans.")

def main():
    """Main execution function."""
    #namespace = os.getenv("NAMESPACE", "openshift-mtv")
    namespace = "openshift-mtv"

    try:
        #host, token, ca_cert = get_k8s_api_info()
        host, token, namespace = get_ocp_api_info()
        #plans = get_mtv_plans(host, token, ca_cert, namespace)
        plans = get_mtv_plans(host, token, namespace)
        validate_plans(plans)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        exit(1)
    except FileNotFoundError as e:
        print(f"Authentication setup failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()