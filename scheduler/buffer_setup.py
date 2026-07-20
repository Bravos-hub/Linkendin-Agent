#!/usr/bin/env python3
"""One-time helper: fetch your Buffer organization and channels via the
GraphQL API so you can copy the LinkedIn channel ID.

Usage:
  BUFFER_API_KEY=... python3 scheduler/buffer_setup.py

Get an API key at https://publish.buffer.com/settings/api
Then add two GitHub repo secrets: BUFFER_API_KEY and BUFFER_CHANNEL_ID.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://api.buffer.com"


def gql(query, key):
    req = urllib.request.Request(
        ENDPOINT,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        data=json.dumps({"query": query}).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()[:500]}")


def main():
    key = os.environ.get("BUFFER_API_KEY") or sys.exit("BUFFER_API_KEY missing")

    # step 1: account -> organizations
    resp = gql("query { account { id email name organizations { id name } } }", key)
    if resp.get("errors"):
        sys.exit(f"graphql errors: {json.dumps(resp['errors'])[:500]}")
    account = (resp.get("data") or {}).get("account") or {}
    orgs = account.get("organizations") or []
    if not orgs:
        print("unexpected response shape — raw:")
        print(json.dumps(resp, indent=2)[:2000])
        sys.exit(0)
    print(f"account: {account.get('name')} <{account.get('email')}>")
    for o in orgs:
        print(f"  organization: {o.get('name')}  id: {o.get('id')}")

    # step 2: channels for the first organization
    org_id = orgs[0]["id"]
    query = (
        "query { channels(input: { organizationId: "
        + json.dumps(org_id)
        + " }) { id name service isQueuePaused } }"
    )
    resp = gql(query, key)
    if resp.get("errors"):
        sys.exit(f"graphql errors: {json.dumps(resp['errors'])[:500]}")
    channels = (resp.get("data") or {}).get("channels")
    if not channels:
        print("unexpected channels shape — raw:")
        print(json.dumps(resp, indent=2)[:2000])
        sys.exit(0)

    print(f"\nchannels in '{orgs[0].get('name')}':")
    for c in channels:
        paused = " (queue paused)" if c.get("isQueuePaused") else ""
        print(f"  {c.get('service', '?'):12} {c.get('name', ''):30} id: {c.get('id')}{paused}")
    print("\nCopy the LinkedIn channel's id into the BUFFER_CHANNEL_ID repo secret.")


if __name__ == "__main__":
    main()
