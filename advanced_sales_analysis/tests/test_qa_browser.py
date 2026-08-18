# -*- coding: utf-8 -*-
"""Step 07 — verifikasi di browser Chrome headless sungguhan (Mode E).

KENAPA `browser_js` DAN BUKAN `start_tour`:
`start_tour()` mensyaratkan file Tour JS terdaftar di bundle `web.assets_tests`, yang berarti
menambah key `assets` ke `__manifest__.py` modul. Modul ini sama sekali tidak punya key `assets`
(`'data': []`, tidak ada static asset apa pun yang didaftarkan) — menambahkannya berarti mengubah
file modul di luar `tests/`, yang ada di luar mandat BACKFILL ("hanya boleh menambah file test").
`HttpCase.browser_js()` memberi lapisan bukti yang SAMA (Chrome headless asli, webclient OWL asli,
klik asli) tanpa menyentuh manifest — kodenya dikirim sebagai string dari Python.
Lihat `doc-dev/backfill/test/07_QA_TESTING.md` §2 dan FINDINGS.md F-18.

Tiga pelajaran dari sesi BACKFILL sebelumnya di modul ini dipakai langsung di sini
(`doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md`):
- CAND-05: action Sales Analysis default membuka **Graph view**, bukan Pivot — harus klik
  switcher `button.o_switch_view.o_pivot` dulu.
- CAND-02: dropdown OWL terbuka pakai class `.o-dropdown--menu`, BUKAN `.dropdown-menu.show`.
- CAND-01: tidak relevan di sini (itu soal API Tour di Odoo 16), tapi jadi alasan tambahan kenapa
  jalur `browser_js` lebih tahan-versi.
"""

from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.fields import Command


JS_CEK_MEASURES = """
(async function () {
    const delay = (ms) => new Promise((r) => setTimeout(r, ms));
    async function waitFor(selector, label, timeout) {
        const start = Date.now();
        while (Date.now() - start < (timeout || 30000)) {
            const el = document.querySelector(selector);
            if (el) { return el; }
            await delay(200);
        }
        throw new Error("timeout menunggu " + (label || selector) + " (" + selector + ")");
    }
    try {
        await waitFor(".o_control_panel", "control panel");

        // CAND-05: action ini default ke Graph view -> pindah ke Pivot dulu.
        const pivotSwitch = await waitFor("button.o_switch_view.o_pivot", "switcher pivot");
        pivotSwitch.click();
        await waitFor(".o_pivot table", "tabel pivot");

        // Tombol Measures ada di `.o_pivot_buttons` (dirender Renderer lewat
        // `web.PivotView.Buttons` -> `web.ReportViewMeasures`), BUKAN di `.o_control_panel`.
        // Dikonfirmasi dengan membaca `web/static/src/views/pivot/pivot_controller.xml` +
        // `web/static/src/views/view.xml` di image odoo:17.0.
        const buttonBar = await waitFor(".o_pivot_buttons", "toolbar pivot");
        const buttons = Array.from(buttonBar.querySelectorAll("button"));
        const measureBtn = buttons.find((b) => b.textContent.trim().startsWith("Measures"));
        if (!measureBtn) {
            throw new Error(
                "tombol Measures tidak ditemukan di .o_pivot_buttons. Tombol yang ada: "
                + buttons.map((b) => b.textContent.trim()).join(" | ")
            );
        }
        measureBtn.click();

        // CAND-02: menu OWL terbuka pakai .o-dropdown--menu, bukan .dropdown-menu.show.
        const menu = await waitFor(".o-dropdown--menu", "dropdown Measures");
        const items = Array.from(menu.querySelectorAll(".o_menu_item"));
        const labels = items.map((e) => e.textContent.trim());
        const wajib = ["Amount Received", "Waiting for Payment", "Amount To Invoice"];
        for (const label of wajib) {
            if (!labels.includes(label)) {
                throw new Error(
                    "measure '" + label + "' TIDAK ada di dropdown. Yang ada: " + labels.join(" | ")
                );
            }
        }

        // Pilih Amount Received dan pastikan kolomnya benar-benar muncul di tabel pivot.
        const target = items.find((e) => e.textContent.trim() === "Amount Received");
        target.click();
        await delay(2000);
        const head = document.querySelector(".o_pivot thead");
        if (!head || !head.textContent.includes("Amount Received")) {
            throw new Error(
                "kolom 'Amount Received' tidak muncul di header pivot. Isi header: "
                + (head ? head.textContent.trim() : "<thead tidak ada>")
            );
        }

        console.log("test successful");
    } catch (err) {
        console.error("BACKFILL browser check gagal: " + err.message);
    }
})();
"""


@tagged('post_install', '-at_install')
class TestAsaQaBrowser(HttpCase):

    def setUp(self):
        super().setUp()
        # Data supaya pivot Sales Analysis tidak kosong — murni transaksi test.
        product = self.env['product.product'].create({
            'name': 'ASA QA Product',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })
        partner = self.env['res.partner'].create({'name': 'ASA QA Partner'})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        self.env.flush_all()

    def test_qa_measures_baru_tersedia_di_pivot_sales_analysis(self):
        """AC-01-02: ketiga measure baru muncul dan benar-benar bisa dipakai di pivot."""
        action = self.env.ref('sale.action_order_report_all')
        self.browser_js(
            "/web#action=%s" % action.id,
            JS_CEK_MEASURES,
            "odoo.isReady === true",
            login="admin",
            timeout=120,
        )
