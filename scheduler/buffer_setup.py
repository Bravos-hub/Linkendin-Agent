#!/usr/bin/env python3
"""One-time helper: list your Buffer channels via the GraphQL API
so you can copy the LinkedIn channel ID.

Usage:
  BUFFER_API_KEY=... python3 scheduler/buffer_setup.py

Get an API key at https://publish.buffer.com/settings/api
Then add two GitHub repo secrets: BUFFER_API_KEY and BUFFER_CHANNEL_ID.
If the response shape looks different (API is in beta), paste the raw
output and adapt — or find the channel ID in Buffer's API Explorer.
"""
import json
import os
import sys
import urllib.request
import urllib.error

key = os.environ.get("BUFFER_API_KEY") or sys.exit("BUFFER_API_KEY missing")
query = "query { channels { id name service } }"
req = urllib.request.Request(
    "https://api.buffer.com",
    method="POST",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    data=json.dumps({"query": query}).encode(),
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
except urllib.error.HTTPError as e:
    sys.exit(f"API error {e.code}: {e.read().decode()[:500]}")

channels = (resp.get("data") or {}).get("channels")
if not channels:
    print("unexpected response shape (beta API) — raw response:")
    print(json.dumps(resp, indent=2)[:2000])
    sys.exit(0)

for c in channels:
    print(f"{c.get('service', '?'):12} {c.get('name', ''):30} id: {c.get('id')}")
print("\nCopy the LinkedIn channel's id into the BUFFER_CHANNEL_ID repo secret.")
