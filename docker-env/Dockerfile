# Diinstansiasi dari doc-dev-backfill/templates/Dockerfile.template (2026-08-18), diadaptasi untuk
# migration-tool Step 6 G1 (2026-08-21): base image dinaikkan ke odoo:18.0 (target migrasi).
# Dipasang SEJAK AWAL (bukan ditambahkan belakangan saat Step 07) supaya tidak terjadi transisi
# `image:` -> `build:` di tengah jalan, yang terbukti bikin filestore ir.attachment hilang
# sementara volume Postgres tetap ada (records/advanced_sales_analysis/SUMMARY.md CAND-04).
#
# FIX 2026-08-21 (G1 run #1 gagal): `pip3 install websocket-client` polos gagal di odoo:18.0
# (`error: externally-managed-environment`, PEP 668 — base Ubuntu 18.0 lebih baru dari 17.0).
# Ini persis lesson 2026-07-29 `purchase_product_optional` yang SUDAH terdokumentasi di
# `migration-tool/templates/Dockerfile.template` (pola fallback `--break-system-packages || `),
# tapi Dockerfile project ini diinstansiasi dari versi doc-dev-backfill yang lebih lama tanpa
# fallback ini — pola fallback WAJIB dipakai (bukan salah satu arah saja) karena image lama
# (17.0) TIDAK KENAL flag itu, sementara image baru (18.0+) MEWAJIBKANNYA.
FROM odoo:18.0
USER root
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && (pip3 install --break-system-packages websocket-client || pip3 install websocket-client)
USER odoo
