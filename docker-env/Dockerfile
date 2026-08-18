# Diinstansiasi dari doc-dev-backfill/templates/Dockerfile.template (2026-08-18).
# Dipasang SEJAK AWAL (bukan ditambahkan belakangan saat Step 07) supaya tidak terjadi transisi
# `image:` -> `build:` di tengah jalan, yang terbukti bikin filestore ir.attachment hilang
# sementara volume Postgres tetap ada (records/advanced_sales_analysis/SUMMARY.md CAND-04).
FROM odoo:17.0
USER root
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && pip3 install websocket-client \
    && rm -rf /var/lib/apt/lists/*
USER odoo
