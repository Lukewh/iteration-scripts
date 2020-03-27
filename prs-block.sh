#!/bin/bash

: '
In your i3blocks configuration to update every 30 minutes

# Prs
[open_prs]
command=PATH_TO_THIS_SCRIPT/prs-block.sh $button
label=
interval=1800
'

source "${BASH_SOURCE%/*}/.env"

FILTERS=(
    "is:pr"
    "is:open"
    "archived:false"
)

REPOS=(
    "repo:canonical-web-and-design/snapcraft.io"
    "repo:canonical-web-and-design/build.snapcraft.io"
    "repo:canonical-web-and-design/charmhub.io"
    "repo:canonical-web-and-design/snap-squad"
    "repo:canonical-web-and-design/snapcraft-poller-script"
)

url="https://github.com/search?q=${FILTERS[*]} ${REPOS[*]}"

if [ $# -eq 1 ]; then
    sensible-browser "${url// /%20}"
fi

query='{"query":"{search(query: \"FILTERS REPOS\", type: ISSUE, last: 20) {edges {node {... on PullRequest {state}}}}}"}'

query=${query/FILTERS/${FILTERS[*]}}
query=${query/REPOS/${REPOS[*]}}

THE_DATA=$(curl --silent \
  --request POST \
  --url https://api.github.com/graphql \
  --header "authorization: Bearer  $GITHUB_ACCESS_TOKEN" \
  --header "content-type: application/json" \
  --data "$query")

# I need to somehow add a space if the count is below 10 :shrug: for another day
echo $THE_DATA | jq '[.data.search.edges[] | if .node.state == "OPEN" then 1 else 0 end] | add'
