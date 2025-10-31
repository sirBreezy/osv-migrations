#!/usr/bin/env sh

set -eu

NAMESPACE="openshift-mtv" 

echo "Fetching all Migration Plans in namespace ${NAMESPACE}..."

oc get plans.forklift.konveyor.io -n ${NAMESPACE} -o json > plans.json

# Check if any plans exist
if [ ! $(jq '.items | length' plans.json) -gt 0 ]; then
  echo "No MTV plans found. Validation successful."
  exit 0
fi

# Build a list of all VMs and the plans they belong to
ALL_VMS=$(jq -r '.items[] | {plan: .metadata.name, vms: .spec.vms | map(.name)} | @json' plans.json)

declare -A vm_counts

# Iterate over each plan and its VMs
echo "${ALL_VMS}" | while read -r plan_details; do
  PLAN_NAME=$(echo "${plan_details}" | jq -r '.plan')
  VM_LIST=$(echo "${plan_details}" | jq -r '.vms[]')

  for vm_name in ${VM_LIST}; do
    # Increment the count for each VM
    if [[ -z "${vm_counts[${vm_name}]}" ]]; then
      vm_counts[${vm_name}]="${PLAN_NAME}"
    else
      vm_counts[${vm_name}]="${vm_counts[${vm_name}]},${PLAN_NAME}"
    fi
  done
done

DUPLICATE_FOUND=false
# Check for any VM that appears in more than one plan
for vm_name in "${!vm_counts[@]}"; do
  plan_list="${vm_counts[${vm_name}]}"
  plan_count=$(echo "${plan_list}" | tr ',' '\n' | wc -l)
  if [[ "${plan_count}" -gt 1 ]]; then
    echo "Error: VM '${vm_name}' is found in multiple plans: ${plan_list}"
    DUPLICATE_FOUND=true
  fi
done

if [ "${DUPLICATE_FOUND}" = true ]; then
  echo "Validation failed: Duplicate VMs found across multiple plans."
  exit 1
else
  echo "Validation successful: No VMs are found in multiple plans."
fi