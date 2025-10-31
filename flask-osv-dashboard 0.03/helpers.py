import requests
from config import CLUSTER_URL, HEADERS, PROMETHEUS_URL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_vms():
    """Fetch all VMs across all namespaces"""
    url = f"{CLUSTER_URL}/apis/kubevirt.io/v1/virtualmachines"
    resp = requests.get(url, headers=HEADERS, verify=False)
    print("Status code:", resp.status_code)
    print("Response:", resp.text)
    resp.raise_for_status()
    data = resp.json()

    vms = []
    for vm in data.get("items", []):
        vms.append({
            "name": vm["metadata"]["name"],
            "namespace": vm["metadata"]["namespace"],
            "status": vm["status"].get("printableStatus", "Unknown"),
            "ready": vm["status"].get("ready", False),
            "runStrategy": vm["spec"].get("runStrategy", "Unknown"),
        })
    return vms

def query_prometheus(query):
    """Query Prometheus for CPU or memory"""
    url = f"{PROMETHEUS_URL}/api/v1/query"
    resp = requests.get(url, params={"query": query}, headers=HEADERS, verify=False)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("result", [])

def enrich_vms_metrics(vms):
    """Attach CPU/Memory usage from Prometheus"""
    # Query CPU in cores
    cpu_results = query_prometheus('sum(rate(container_cpu_usage_seconds_total{container="virt-launcher"}[2m])) by (pod, namespace)')
    cpu_map = {(r["metric"]["namespace"], r["metric"]["pod"]): float(r["value"][1]) for r in cpu_results}

    # Query memory in bytes
    mem_results = query_prometheus('sum(container_memory_working_set_bytes{container="virt-launcher"}) by (pod, namespace)')
    mem_map = {(r["metric"]["namespace"], r["metric"]["pod"]): float(r["value"][1]) for r in mem_results}

    for vm in vms:
        pod_name = f"virt-launcher-{vm['name']}"
        ns = vm["namespace"]
        vm["cpu"] = cpu_map.get((ns, pod_name), 0)
        vm["memory"] = mem_map.get((ns, pod_name), 0)

    return vms

print(get_vms)