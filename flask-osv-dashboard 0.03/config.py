CLUSTER_URL = "https://api.ocp800.thebrizzles.local:6443"
TOKEN = "sha256~JQ6L_eGCHzkisaatko9UeOI14TXZ-cixVTnV-A7R9Ik"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

PROMETHEUS_URL = f"{CLUSTER_URL}/apis/route.openshift.io/v1/namespaces/openshift-monitoring/routes/prometheus-k8s"
PROMETHEUS_HEADERS = HEADERS  # Use the same token