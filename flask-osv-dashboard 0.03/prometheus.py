# prometheus.py
import requests
import os

API_TOKEN = os.getenv("PROM_TOKEN", "sha256~JQ6L_eGCHzkisaatko9UeOI14TXZ-cixVTnV-A7R9Ik")
PROM_URL = os.getenv(
    "PROM_URL",
    "https://api.ocp800.thebrizzles.local:6443/apis/route.openshift.io/v1/namespaces/openshift-monitoring/routes/prometheus-k8s"
)
PROM_HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def query_prometheus(query: str):
    """Send a query to Prometheus and return results."""
    try:
        resp = requests.get(
            PROM_URL,
            headers=PROM_HEADERS,
            params={"query": query},
            verify=False,
            timeout=5,
        )
        if resp.status_code != 200:
            print("Prometheus error:", resp.text)
            return []
        return resp.json().get("data", {}).get("result", [])
    except Exception as e:
        print("Prometheus request failed:", e)
        return []

def get_vm_metrics(vm_name: str, namespace: str):
    """Return CPU (cores) and Memory (bytes) usage for a VM."""
    cpu_query = f'rate(kubevirt_vmi_cpu_usage_seconds_total{{namespace="{namespace}", name="{vm_name}"}}[2m])'
    mem_query = f'kubevirt_vmi_memory_resident_bytes{{namespace="{namespace}", name="{vm_name}"}}'

    cpu = query_prometheus(cpu_query)
    mem = query_prometheus(mem_query)

    return {
        "cpu": float(cpu[0]["value"][1]) if cpu else 0,
        "memory": int(mem[0]["value"][1]) if mem else 0,
    }
