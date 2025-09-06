#!/usr/bin/env bash
set -euo pipefail

mysql -uroot -p"$MYSQL_ROOT_PASSWORD" linebot_test        < /schemas/schema_linebot.sql       || { echo "[init] linebot_test import failed"; exit 1; }
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" GenAI_verify_test   < /schemas/schema_verify.sql        || { echo "[init] verify_test import failed"; exit 1; }
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" review_system_test  < /schemas/schema_rs.sql            || { echo "[init] review_system_test import failed"; exit 1; }

echo "[init] schema imports done."
