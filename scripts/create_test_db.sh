#!/usr/bin/env bash
set -euo pipefail

DB_NAME="onlinetlabs_test"

if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
  echo "Database '$DB_NAME' already exists, skipping."
else
  createdb -U postgres "$DB_NAME"
  echo "Database '$DB_NAME' created."
fi
