#!/bin/bash

curl --http1.1 -X POST https://agentcore-d806c888.auth.us-east-1.amazoncognito.com/oauth2/token \
     -H "Content-Type: application/x-www-form-urlencoded"  \
     -d "grant_type=client_credentials&client_id=35ik1sng2lufmvp5iq65d2e0kt&client_secret=1gkp1hjprck6s96r9p36qs4di2b9la2na0rgerk8bbmj55e4g3h9"



