#!/bin/sh
set -eu
: "${UPSTREAM_PREFIX:=stg}"
TEMPLATE=/etc/nginx/conf.d/app.conf.template
TARGET=/etc/nginx/conf.d/app.conf
if [ -f "$TEMPLATE" ]; then
  echo "[entrypoint] Generating $TARGET (UPSTREAM_PREFIX=$UPSTREAM_PREFIX)"
  envsubst '${UPSTREAM_PREFIX}' < "$TEMPLATE" > "$TARGET"
else
  echo "[entrypoint] Template $TEMPLATE not found (skip)"
fi
exec nginx -g 'daemon off;'
