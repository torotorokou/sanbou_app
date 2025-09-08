# startup_preflight.py
import os
import sys
import json
from pathlib import Path
from google.cloud import storage  # type: ignore

def main():
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred or not Path(cred).is_file():
        print("[ERROR] key file missing:", cred)
        sys.exit(91)

    try:
        ce = json.load(open(cred)).get("client_email")
        print("[INFO] key client_email:", ce)
    except Exception as e:
        print("[ERROR] parse key failed:", e)
        sys.exit(92)

    bucket_name = os.environ.get("GCS_BUCKET_NAME", "sanbouapp-stg")
    print("[INFO] target bucket:", bucket_name)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        print("[ERROR] bucket not accessible (exists()=False):", bucket_name)
        sys.exit(93)
    print("[INFO] bucket exists OK")

    try:
        it = client.list_blobs(bucket_name, max_results=1)
        next(iter(it), None)
        print("[INFO] list_blobs OK")
    except Exception as e:
        print("[ERROR] list_blobs failed:", e)
        sys.exit(94)

    print("[INFO] GCS preflight success")

if __name__ == "__main__":
    main()
