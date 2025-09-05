#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/stg-key.json"
gcloud storage cp -r gs://sanboapp-stg/customer ./data/
