# Diinstansiasi dari doc-dev-backfill/templates/Dockerfile.template (2026-08-18), diadaptasi untuk
# migration-tool Step 6 G1 (2026-08-21): base image dinaikkan ke odoo:18.0 (target migrasi saat itu).
# Dipasang SEJAK AWAL (bukan ditambahkan belakangan saat Step 07) supaya tidak terjadi transisi
# `image:` -> `build:` di tengah jalan, yang terbukti bikin filestore ir.attachment hilang
# sementara volume Postgres tetap ada.
#
# UPDATE 2026-08-26 (project migrasi 18.0->19.0): base image dinaikkan ke odoo:19.0. Tag ini
# BELUM diverifikasi tersedia di Docker Hub oleh AI (tidak ada akses jaringan di sesi ini) —
# kalau `docker compose build` gagal dengan "manifest not found"/"pull access denied", ini
# indikasi tag resmi belum/berbeda nama, bukan kesalahan Dockerfile lain. Pola fallback
# `pip3 install --break-system-packages ... || pip3 install ...` (lesson 2026-07-29
# `purchase_product_optional`, WAJIB dipakai kedua arah, bukan salah satu) dipertahankan apa
# adanya dari versi 18.0 — kemungkinan besar masih perlu untuk 19.0 (base Ubuntu image Odoo
# biasanya makin baru per major version, PEP 668 externally-managed-environment kemungkinan
# masih berlaku), belum dikonfirmasi eksekusi langsung.
FROM odoo:19.0
USER root
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg ca-certificates \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && (pip3 install --break-system-packages websocket-client || pip3 install websocket-client)
USER odoo
