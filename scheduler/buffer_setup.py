#!/usr/bin/env python3
"""One-time helper: list your Buffer channels so you can copy the LinkedIn profile ID.

Usage:
  BUFFER_ACCESS_TOKEN=... python3 scheduler/buffer_setup.py

Get a token at https://buffer.com/developers/apps/create (create an app, copy its access token).
Then add both values as GitHub repo secrets: BUFFER_ACCESS_TOKEN and BUFFER_PROFILE_ID.
"""
import json
import os
import sys
import urllib.request

token = os.environ.get("BUFFER_ACCESS_TOKEN") or sys.exit("BUFFER_ACCESS_TOKEN missing")
req = urllib.request.Request(f"https://api.bufferapp.com/1/profiles.json?access_token={token}")
with urllib.request.urlopen(req) as r:
    profiles = json.loads(r.read())

for p in profiles:
    print(f"{p['service']:12} {p.get('service_username') or p.get('formatted_username', ''):30} id: {p['id']}")
print("\nCopy the LinkedIn channel's id into the BUFFER_PROFILE_ID repo secret.")
