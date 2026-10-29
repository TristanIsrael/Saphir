# GitHub Project Management via GraphQL API

## Context

The Saphir Kanban is a **Project V2** (new Projects experience) on GitHub. The `gh` CLI's `--project` and `--project-status` flags only work with **classic projects**, which are deprecated. All project management must be done via the **GraphQL API**.

## Project Constants

| Constant | Value | How to discover |
|---|---|---|
| Project ID | `PVT_kwHOAFaMw84A78Wv` | Query below |
| Project number | `5` | `gh api graphql` query below |
| Status field ID | `PVTSSF_lAHOAFaMw84A78WvzgwFz-M` | Query below |
| Repo owner | `TristanIsrael` | — |
| Repo name | `Saphir` | — |

### Discover project ID

```bash
gh api graphql -f query='
query {
  repository(owner: "TristanIsrael", name: "Saphir") {
    projectV2(number: 5) {
      id
      title
    }
  }
}'
```

### Discover field IDs and option IDs

```bash
gh api graphql -f query='
query {
  repository(owner: "TristanIsrael", name: "Saphir") {
    projectV2(number: 5) {
      fields(first: 10) {
        nodes {
          ... on ProjectV2SingleSelectField {
            name
            id
            options { id name }
          }
        }
      }
    }
  }
}'
```

Status option IDs:

| Status | Option ID |
|---|---|
| Backlog | `9e5b0785` |
| Analysis needed | `a5abc1ee` |
| Not ready | `cd447b79` |
| Ready | `f75ad846` |
| In Progress | `47fc9ee4` |
| In review | `7857e29c` |
| Validated | `b5b7abc6` |
| Done | `98236657` |

## Operations

### 1. Create an issue with labels

```bash
gh issue create \
  --title "Title" \
  --body "Body" \
  --label "gui" --label "technical debt"
```

### 2. Add an issue to the project

First get the issue's `node_id`, then call `addProjectV2ItemById`:

```bash
# Get node_id
ISSUE_NODE_ID=$(gh api repos/TristanIsrael/Saphir/issues/<NUMBER> --jq '.node_id')

# Add to project
gh api graphql -f query="
mutation {
  addProjectV2ItemById(
    input: {
      projectId: \"PVT_kwHOAFaMw84A78Wv\"
      contentId: \"$ISSUE_NODE_ID\"
    }
  ) {
    item { id }
  }
}"
```

The response contains the **item ID** (e.g. `PVTI_lAHOAFaMw84A78WvzhEcPME`) — save it for the next step.

### 3. Set the project status field

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwHOAFaMw84A78Wv"
      itemId: "PVTI_lAHOAFaMw84A78WvzhEcPME"
      fieldId: "PVTSSF_lAHOAFaMw84A78WvzgwFz-M"
      value: { singleSelectOptionId: "7857e29c" }
    }
  ) {
    projectV2Item { id }
  }
}'
```

Replace:
- `itemId` → the item ID from step 2 (or discovered via step 4)
- `singleSelectOptionId` → the desired status option ID (table above)

### 4. Look up an existing item ID for an issue

If you don't have the item ID, query it from the issue:

```bash
gh api graphql -f query='
query {
  repository(owner: "TristanIsrael", name: "Saphir") {
    issue(number: <NUMBER>) {
      number
      projectItems(first: 1) {
        nodes {
          id
          fieldValues(first: 5) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
          }
        }
      }
    }
  }
}'
```

### 5. Verify an issue's project status

Same query as step 4. The `name` under `ProjectV2ItemFieldSingleSelectValue` is the current status.

### 6. Batch-verify multiple issues

```bash
gh api graphql -f query='
query {
  repository(owner: "TristanIsrael", name: "Saphir") {
    i1: issue(number: 129) { number projectItems(first: 1) { nodes { fieldValues(first: 5) { nodes { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } }
    i2: issue(number: 130) { number projectItems(first: 1) { nodes { fieldValues(first: 5) { nodes { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } }
  }
}' --jq '.data.repository | to_entries[] | "\(.key): #\(.value.number) → \(.value.projectItems.nodes[0].fieldValues.nodes[]? | select(.name) | .name // "N/A")"'
```

## Helper script (one-shot: add issue + set status)

```bash
#!/usr/bin/env bash
# usage: add_to_kanban.sh <issue_number> <status_option_id>
# example: add_to_kanban.sh 139 7857e29c

set -euo pipefail

ISSUE_NUM="$1"
STATUS_ID="${2:-7857e29c}"  # default: In review
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
echo "Issue #${ISSUE_NUM} added to Kanban with status set."
```

## Valid labels

`bug`, `documentation`, `duplicate`, `feature`, `wontfix`, `performance`, `gui`, `security`, `technical debt`, `UX/UI`, `testing`

## Rules

- Every code commit must be linked to a GitHub issue.
- Search existing issues first; create a new one only if none fits.
- Ask the user for validation **before** creating an issue.
- One commit = one issue (atomic commits).
- Label every issue at creation time (component + type).
- Every issue must be added to the **Saphir Kanban** project.
- Status must reflect actual state. **Never close issues** — max status is "In review" until the user validates.
