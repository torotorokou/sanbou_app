SELECT nspname AS schema_name
FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%'
  AND nspname <> 'information_schema';