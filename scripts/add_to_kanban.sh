#!/usr/bin/env bash
# Add a GitHub issue to the Saphir Kanban (Project V2) and set its status.
#
# usage: add_to_kanban.sh <issue_number> [status_option_id]
# example: add_to_kanban.sh 139 7857e29c   # status = "In review"
#
# Status option IDs:
#   Backlog          9e5b0785
#   Analysis needed  a5abc1ee
#   Not ready        cd447b79
#   Ready            f75ad846
#   In Progress      47fc9ee4
#   In review        7857e29c
#   Validated        b5b7abc6
#   Done             98236657

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $(basename "$0") <issue_number> [status_option_id]"
  echo "default status: In review (7857e29c)"
  exit 1
fi

ISSUE_NUM="$1"
STATUS_ID="${2:-7857e29c}"
PROJECT_ID="PVT_kwHOAFaMw84A78Wv"
FIELD_ID="PVTSSF_lAHOAFaMw84A78WvzgwFz-M"
OWNER="TristanIsrael"
REPO="Saphir"

# 1. Get issue node_id
NODE_ID=$(gh api "repos/${OWNER}/${REPO}/issues/${ISSUE_NUM}" --jq '.node_id')
echo "Issue #${ISSUE_NUM} node_id: ${NODE_ID}"

# 2. Add to project, capture item ID
ITEM_ID=$(gh api graphql -f query="
mutation {
  addProjectV2ItemById(input: {projectId: \"${PROJECT_ID}\", contentId: \"${NODE_ID}\"}) {
    item { id }
  }
}" --jq '.data.addProjectV2ItemById.item.id')
echo "Project item ID: ${ITEM_ID}"

# 3. Set status
gh api graphql -f query="
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: \"${PROJECT_ID}\"
    itemId: \"${ITEM_ID}\"
    fieldId: \"${FIELD_ID}\"
    value: { singleSelectOptionId: \"${STATUS_ID}\" }
  }) {
    projectV2Item { id }
  }
}" > /dev/null

echo "Issue #${ISSUE_NUM} added to Saphir Kanban (status set)."
