#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=app_password="$METABASE_DB_PASSWORD" --set=reader_password="$BI_READER_PASSWORD" <<'SQL'
CREATE ROLE metabase_app LOGIN PASSWORD :'app_password';
CREATE ROLE bi_reader LOGIN PASSWORD :'reader_password';
CREATE DATABASE metabase OWNER metabase_app;
CREATE DATABASE unitalent_analytics;
REVOKE ALL ON DATABASE unitalent_analytics FROM PUBLIC;
GRANT CONNECT ON DATABASE unitalent_analytics TO bi_reader;
SQL
