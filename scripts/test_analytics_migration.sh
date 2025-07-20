#!/bin/bash
# Test the macro_analytics_results migration

set -e

DB_FILE="/tmp/test_macro_analytics.db"
MIGRATION_FILE="$(dirname "$0")/../migrations/001_create_analytics_table.sql"

# Remove old test db if exists
rm -f "$DB_FILE"

# Apply migration
sqlite3 "$DB_FILE" < "$MIGRATION_FILE"

echo "--- Table Schema ---"
sqlite3 "$DB_FILE" ".schema macro_analytics_results"

echo "--- Indexes ---"
sqlite3 "$DB_FILE" "PRAGMA index_list('macro_analytics_results');"

# Clean up
echo "\nTest DB at: $DB_FILE (delete manually if you want to inspect)" 