#!/bin/bash

if [[ -z "${CLIENT_ID}" || -z "${CLIENT_SECRET}" ]]; then
  echo "Usage: export CLIENT_ID=... CLIENT_SECRET=...; $0" >&2
  exit 1
fi

curl --http1.1 -X POST https://agentcore-d806c888.auth.us-east-1.amazoncognito.com/oauth2/token \
     -H "Content-Type: application/x-www-form-urlencoded"  \
     -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}"



