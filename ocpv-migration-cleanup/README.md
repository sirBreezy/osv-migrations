# ocpv-migration-cleanup

To create a Tekton task using Python and the
requests library, you will need to perform API calls to the Kubernetes/OpenShift API server from within the task's container. The best way to do this is by leveraging the in-cluster service account credentials, which are automatically mounted into every pod. This eliminates the need for manual authentication with usernames, passwords, or tokens. 

Here's a complete, step-by-step guide with the necessary YAML files and Python script.

## Prerequisites

- OpenShift Pipelines Operator is installed on your cluster.
- Migration Toolkit for Virtualization (MTV) is installed and configured.
- The `tekton-pipelines` namespace has a `ServiceAccount` with permissions to list `Plan` custom resources.
- You will use an image with Python and the `requests` library. For this example, we will use a base Python image and install `requests` within the task step itself. 

Step 1: Write the Python script
This script will be embedded directly into the Tekton Task. It will query the Kubernetes API, which is accessible from within the container via an automatically provided service account token. 
validate_mtv_plans.py

### 1. Deploy the Task and Pipeline:

```bash
$ oc apply -f validate-mtv-plan-uniqueness-python.yaml

$ oc apply -f mtv-validation-resources.yaml
```    

### 2. Start the `PipelineRun` to trigger the validation:

```bash    
oc create -f mtv-validation-pipelinerun.yaml
```    

### 3. Check the logs:

To see the output, find the most recent PipelineRun and 
check its logs.

```
# Find the name of the most recent PipelineRun
oc get pipelineruns -l tekton.dev/pipeline=mtv-validation-pipeline -o name | tail -n 1

# Get the logs for the 'run-validation' step

oc logs -f $(oc get pipelineruns -l tekton.dev/pipeline=mtv-validation-pipeline -o name | tail -n 1) -c ste```p-run-validation
```

What the script does:

- It retrieves all Plan custom resources from the openshift-mtv namespace and outputs them as JSON.
- It uses jq to extract the name of each plan and the name of each VM within that plan.
- It builds an associative array (vm_counts) to track which plans each VM appears in.
- It then iterates through the array to check if any VM is associated with more than one plan.
- If a duplicate is found, it prints an error message and exits with a non-zero status code, causing the Tekton task to fail.


## Using python with the request library

To create a Tekton task using Python and the requests library, you will need to perform API calls to the Kubernetes/OpenShift API server from within the task's container. The best way to do this is by leveraging the in-cluster service account credentials, which are automatically mounted into every pod. This eliminates the need for manual authentication with usernames, passwords, or tokens.

## Prerequisites

- OpenShift Pipelines Operator is installed on your cluster.
- Migration Toolkit for Virtualization (MTV) is installed and configured.
- The tekton-pipelines namespace has a ServiceAccount with permissions to list Plan custom resources.
- You will use an image with Python and the requests library. For this example, we will use a base Python image and install requests within the task step itself.

### Step 1: Write the Python script

This script will be embedded directly into the Tekton Task. It will query the Kubernetes API, which is accessible from within the container via an automatically provided service account token. 

`validate_mtv_plans.py`

```python
#!/usr/bin/env python3
import os
import json
import requests

def get_k8s_api_info():
    """Retrieves in-cluster Kubernetes API information."""
    #host = "https://kubernetes.default.svc"
    host = "https://apit.ocp800.thebrizzles.local:6443"
    #token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    #ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    token="sha~"
    #if not os.path.exists(token_path):
    #    raise FileNotFoundError("Service account token not found.")
    #
    #with open(token_path, "r") as f:
    #    token = f.read().strip()

    #return host, token, ca_cert_path
    return host, token

# def get_mtv_plans(host, token, ca_cert, namespace):
def get_mtv_plans(host, token, ca_cert, namespace):
    """Fetches all MTV Plan custom resources using the Kubernetes API."""
    url = f"{host}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    print(f"Fetching MTV plans from {url}")
    response = requests.get(url, headers=headers, verify=ca_cert)
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
            print(f"ERROR: VM '{vm_name}' is in multiple plans: {', '.join(plan_list)}")
            duplicate_found = True
    
    if duplicate_found:
        print("Validation failed: Duplicate VMs found across multiple plans.")
        exit(1)
    else:
        print("Validation successful: No VMs are found in multiple plans.")

def main():
    """Main execution function."""
    namespace = os.getenv("NAMESPACE", "openshift-mtv")
    
    try:
        host, token, ca_cert = get_k8s_api_info()
        plans = get_mtv_plans(host, token, ca_cert, namespace)
        validate_plans(plans)
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        exit(1)
    except FileNotFoundError as e:
        print(f"Authentication setup failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
```

### Step 2: Create the Tekton ```Task```

This task will execute the Python script. It uses a Python base image, installs the requests library, and then runs the script. 

```validate-mtv-plan-uniqueness-python.yaml```

```yaml
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: validate-mtv-plan-uniqueness-python
spec:
  params:
    - name: namespace
      description: The namespace where the MTV plans are located.
      default: openshift-mtv
  steps:
    - name: install-deps
      image: python:3.9-slim
      script: |
        #!/bin/sh
        set -eu
        pip install requests

    - name: run-validation
      image: python:3.9-slim
      env:
        - name: NAMESPACE
          value: $(params.namespace)
      script: |
        #!/usr/bin/env python3
        # Start of embedded Python script

        import os
        import json
        import requests
        import sys

        def get_k8s_api_info():
            """Retrieves in-cluster Kubernetes API information."""
            host = "https://kubernetes.default.svc"
            token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
            ca_cert_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
            
            if not os.path.exists(token_path):
                raise FileNotFoundError("Service account token not found.")
            
            with open(token_path, "r") as f:
                token = f.read().strip()
            
            return host, token, ca_cert_path

        def get_mtv_plans(host, token, ca_cert, namespace):
            """Fetches all MTV Plan custom resources using the Kubernetes API."""
            url = f"{host}/apis/forklift.konveyor.io/v1beta1/namespaces/{namespace}/plans"
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            
            print(f"Fetching MTV plans from {url}", file=sys.stderr)
            response = requests.get(url, headers=headers, verify=ca_cert)
            response.raise_for_status()
            
            return response.json()

        def validate_plans(plans):
            """Validates that each VM is in only one migration plan."""
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
                    if vm_name not in vm_plan_map:
                        vm_plan_map[vm_name] = []
                    vm_plan_map[vm_name].append(plan_name)

            duplicate_found = False
            for vm_name, plan_list in vm_plan_map.items():
                if len(plan_list) > 1:
                    print(f"ERROR: VM '{vm_name}' is in multiple plans: {', '.join(plan_list)}", file=sys.stderr)
                    duplicate_found = True
            
            if duplicate_found:
                print("Validation failed: Duplicate VMs found across multiple plans.", file=sys.stderr)
                sys.exit(1)
            else:
                print("Validation successful: No VMs are found in multiple plans.")

        def main():
            namespace = os.getenv("NAMESPACE", "openshift-mtv")
            try:
                host, token, ca_cert = get_k8s_api_info()
                plans = get_mtv_plans(host, token, ca_cert, namespace)
                validate_plans(plans)
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}", file=sys.stderr)
                sys.exit(1)
            except FileNotFoundError as e:
                print(f"Authentication setup failed: {e}", file=sys.stderr)
                sys.exit(1)

        if __name__ == "__main__":
            main()
        
```

### Step 3: Create a ```Pipeline``` and ```ServiceAccount```

```mtv-validation-resources.yaml```

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mtv-validator-sa
  namespace: openshift-mtv

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: mtv-plan-reader
  namespace: openshift-mtv
rules:
  - apiGroups: ["forklift.konveyor.io"]
    resources: ["plans"]
    verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: mtv-plan-reader-binding
  namespace: openshift-mtv
subjects:
  - kind: ServiceAccount
    name: mtv-validator-sa
roleRef:
  kind: Role
  name: mtv-plan-reader
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: mtv-validation-pipeline
spec:
  tasks:
    - name: validate-plans
      taskRef:
        name: validate-mtv-plan-uniqueness-python
      params:
        - name: namespace
          value: openshift-mtv
```

### Step 4: Run the ```Pipeline```

To execute the validation, create a ```PipelineRun```.

```mtv-validation-pipelinerun.yaml```

```yaml
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  name: mtv-validation-run-$(date +%s)
spec:
  pipelineRef:
    name: mtv-validation-pipeline
  serviceAccountName: mtv-validator-sa # Use the service account with the correct permissions
```

export CDI_DEFAULT_VIRT_SC="$(oc get sc -o jsonpath='{.items[?(.metadata.annotations.storageclass\.kubernetes\.io\/is-default-class=="true")].metadata.name}')"

