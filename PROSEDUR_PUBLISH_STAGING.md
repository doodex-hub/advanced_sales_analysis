# Prosedur Publish ke Git Odoo Store: `migration/[versi]` → `staging/[versi]` → `[versi]`

Sumber: bagian "Prosedur per repo" di `publish-staging-git-odoo-store-log.md`, diperkuat dengan pelajaran dari insiden `pos_margin_sale` dan audit manifest `images`.
Tanda **[BARU]** = tambahan penguatan yang tidak ada di log asli (perintah, checklist, verifikasi).

## Gambaran alur

```
migration/[versi]  --(cleaning)-->  staging/[versi]  --(merge)-->  [versi]   (branch publish ke store)
   (kerja/migrasi)                   (bersih, di origin)            (dibaca Odoo Store)
```

Aturan emas:
1. Branch `[versi]` hanya boleh berisi hasil merge dari `staging/[versi]`, tidak pernah dari `migration/[versi]` langsung.
2. Branch lokal **tidak pernah dipercaya** sudah sinkron. Selalu `reset --hard` ke origin sebelum merge.
3. Tiap repo dan versi diperiksa satu per satu. Tidak ada script blind (kecuali pola yang terbukti identik, misalnya fix manifest `images`).
4. SKIP hanya sah setelah dicek (`git ls-tree` + manifest + README), bukan dilewati tanpa cek.

---

## Langkah 0 [BARU] — Pra-syarat per repo

```bash
git status --short                 # harus bersih
git diff --stat                    # kalau banyak "modified", cek insertion == deletion
git checkout -- .                  # HANYA kalau terbukti noise CRLF/LF
git fetch origin --prune
git branch -r | grep -E "staging/|/migration/|origin/[0-9]+\.0$"
git config user.name; git config user.email    # harus abkuncoro18 <38222994+abkuncoro18@users.noreply.github.com>
```

- Noise CRLF/LF: insertion dan deletion sama persis. Jangan ikut ter-commit.
- Kalau `git push` menolak dengan "could not read Password", remote URL belum menyimpan token. Pasang token ke `remote.origin.url` secara terprogram. **Jangan tampilkan token di log atau chat.**
- Jangan `push --force` ke branch `[versi]`. Force-push hanya boleh ke `staging/[versi]` dan hanya atas keputusan eksplisit (preseden: rebuild `pos_margin_sale` 18.0).

## Langkah 0b [BARU] — Bump version (di `migration/[versi]`, sebelum cleaning)

Bump dilakukan di branch kerja `migration/[versi]`, **bukan** di `staging/[versi]` atau `[versi]`.

Alasan:
- Staging hanya hasil cleaning dari `migration/[versi]`. Bump di staging membuat kedua branch tidak konsisten dan merusak verifikasi `diff staging vs publish`.
- Satu-satunya perubahan `version` yang sah di staging adalah **koreksi prefix** (contoh: `17.0.1.0` di branch 16.0 → `16.0.1.0`), bukan bump.

| Situasi | Bump |
|---|---|
| Migrasi ke versi baru | Sekali, ke `[versi].1.0.0` (contoh `20.0.1.0.0`). |
| Bug fix / hotfix setelah rilis | Patch: `20.0.1.0.1`. |
| Fitur baru / perubahan view atau model | Minor: `20.0.1.1.0`. |
| Hanya cleaning atau merge ke branch `[versi]` | **Tidak bump.** |
| Hanya aset store (banner, icon, screenshot, `index.html`) | Opsional. Belum dipastikan apakah store memuat ulang tanpa bump. Cek dulu; kalau tampilan tidak berubah, bump patch lalu ulangi alur staging. |

Aturan:
- Bump **sekali per rilis**, bukan per commit. Setelah itu mengalir ke `staging` dan `[versi]` lewat alur biasa.
- Prefix selalu sama dengan versi branch (`20.0.x.y.z`). Sudah dicek di Langkah 3c.
- Di repo migrasi (kode wajib identik dengan versi sebelumnya), bump hanya untuk perubahan kode yang disengaja dan tercatat (`FINDINGS.md` / hotfix log).
- Urutan: commit bump di `migration/[versi]` → baru lanjut ke Langkah 1.

```bash
git checkout migration/<versi>
# edit <modul>/__manifest__.py : 'version': '<versi>.x.y.z'
git commit -am "bump: <modul> version to <versi>.x.y.z"
```

---

## Langkah 1 — Fetch dan cek branch remote

```bash
git fetch origin
git branch -r | grep "staging/<versi>"      # sudah ada atau belum?
```

Catat dulu keadaan awal (hash `origin/staging/[versi]` dan `origin/[versi]`) untuk kolom `lama→baru` di log.

## Langkah 2 — Buat `staging/[versi]` dari `migration/[versi]`

```bash
# kalau branch lokal migration/[versi] ada:
git checkout -b staging/<versi> migration/<versi>
# kalau tidak ada, pakai remote:
git checkout -b staging/<versi> origin/migration/<versi>
```

- **Skip pembuatan kalau `origin/staging/[versi]` sudah ada.** Catat saja, jangan dibuat ulang. Branch yang sudah ada langsung ke Langkah 3 untuk dicek/dibersihkan.
- **[BARU]** Kalau staging sudah ada, mulai dari `git checkout staging/<versi> && git reset --hard origin/staging/<versi>`.

## Langkah 3 — Cleaning `staging/[versi]`

### 3a. Hapus (di root dan di dalam folder tiap modul, cek keduanya)

| Item | Catatan |
|---|---|
| `CLAUDE.md` | Pernah nyempil **di dalam folder modul** (`purchase_product_optional` 18.0). |
| `doc-dev/` | Pernah tersisa di dalam modul (`purchase_product_optional/doc-dev/`). |
| `docker-env/` | Di root atau di dalam modul. |
| `.claude/settings.json` | Di root. |
| `tests/` | Tiap modul. |
| `README.md` **root** | Hapus untuk batch 18.0/19.0. Untuk 16.0/17.0 diadaptasi, bukan dihapus. Kalau cuma placeholder kosong, hapus. |
| `LICENSE`, `LICENSE.txt`, `LISEZMOI.md` | Root **dan** duplikat di dalam modul. `pin_message` memakai `LICENSE.txt`. |
| File verifikasi Google (`google*.html`) | Root dan di dalam modul. |

### 3b. Sesuaikan (jangan hapus)

- `README.md` **modul**: ubah baris `Odoo version: X` ke versi branch. Salah tulis yang pernah ditemukan: README 16.0 bertuliskan 17.0, README 19.0 bertuliskan 16.0/17.0/18.0. Kalau modul tidak punya README (`sale_margin_threshold`), biarkan.
- `__manifest__.py`:
  - `version` harus berawalan versi branch. Pernah salah: `sale_margin_threshold` 16.0 tertulis `17.0.1.0`.
  - `images` harus persis sesuai file yang ada di `static/description/`:
    ```python
    'images': [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],
    ```
    Cek nama file nyata dulu (`git ls-tree -r HEAD --name-only | grep static/description`). Jangan percaya manifest. Pola salah yang pernah ada: menunjuk `banner.png` padahal yang ada `banner.gif`, dan `icon.png` tidak disebut.

### 3c. [BARU] Checklist bersih sebelum commit

```bash
# 1. Tidak ada sisa file terlarang di path manapun
git ls-files | grep -iE "(^|/)(CLAUDE\.md|doc-dev|docker-env|tests)(/|$)|(^|/)\.claude/|LICENSE|LISEZMOI|google[0-9a-f]+\.html"

# 2. Manifest: versi dan images
grep -nE "'version'|\"version\"" */__manifest__.py
grep -nA3 "images" */__manifest__.py
ls */static/description/ 2>/dev/null

# 3. README modul menyebut versi yang benar
grep -n "Odoo version" */README.md
```

Hasil nomor 1 harus kosong (kecuali LICENSE yang memang sengaja dipertahankan oleh keputusan repo). Nomor 2 dan 3 harus cocok dengan versi branch dan file nyata.

**[BARU] Hati-hati:** `tests/` dihapus di staging. Pastikan tidak ada modul yang `import`/`data` merujuk file di `tests/` atau `doc-dev/` di manifest, kalau tidak modul gagal install di store.

## Langkah 4 — Commit dan push staging

```bash
git add -A
git commit -m "cleaning"                       # pembersihan
# atau:
git commit -m "fix: correct manifest images key to match actual files (banner.gif + icon.png)"
git push origin staging/<versi>
```

- Pesan commit: **bahasa Inggris** (instruksi user untuk batch 16.0/17.0 dan fix manifest).
- **[BARU]** Kalau hasil cleaning kosong (tidak ada yang diubah), **jangan buat commit kosong**. Itu berarti SKIP: catat "sudah bersih" di log.
- **[BARU]** Kalau hasil `git push` adalah `Everything up-to-date` padahal diharapkan ada perubahan, **berhenti dan selidiki**. Itu gejala branch lokal basi (lihat insiden di bawah).

## Langkah 5 — Merge `staging/[versi]` → `[versi]` (LANGKAH KRITIS)

```bash
git fetch origin
git checkout staging/<versi> && git reset --hard origin/staging/<versi>   # WAJIB, jangan dilewati

# branch publish: sinkronkan dulu, atau buat kalau belum ada
git checkout <versi> 2>/dev/null || git checkout -b <versi> staging/<versi>
git reset --hard origin/<versi> 2>/dev/null                               # hanya jika origin/<versi> sudah ada

git merge staging/<versi>                       # fast-forward bila history lurus
git push origin <versi>
```

Catatan:
- Merge biasanya fast-forward. Pengecualian: `purchase_product_optional` 18.0 menghasilkan merge commit karena origin punya history sendiri. Itu wajar, dicatat terpisah.
- **[BARU]** Dilarang merge dari branch lokal yang belum di-reset. Reset ke origin tiap kali, walau sudah fetch di sesi yang sama.

### Insiden yang menjadi dasar aturan ini (`pos_margin_sale` 18.0 dan 19.0)
- Gejala: `git push` bilang "Everything up-to-date".
- Penyebab: `staging/18.0`/`19.0` lokal basi, sehingga merge tidak membawa apa-apa. Padahal `origin/staging` punya 9 commit (186 file gambar) yang belum masuk ke `origin/18.0`/`19.0`.
- Perbaikan: reset staging lokal ke origin, merge ulang, push. Hasil `462eb05→064a480` (18.0) dan `83e6778→bdf62c0` (19.0).

## Langkah 6 [BARU] — Verifikasi akhir (wajib sebelum lapor selesai)

Fetch fresh dulu, lalu bandingkan **remote dengan remote**, bukan branch lokal:

```bash
git fetch origin --prune

# 1. staging dan publish harus identik
git diff origin/staging/<versi> origin/<versi> --stat        # harus kosong

# 2. publish tidak boleh membawa sisa terlarang
git ls-tree -r origin/<versi> --name-only | grep -iE "(^|/)(CLAUDE\.md|doc-dev|docker-env|tests)(/|$)|(^|/)\.claude/|google[0-9a-f]+\.html"

# 3. manifest di origin/<versi> (bukan staging)
git show origin/<versi>:<modul>/__manifest__.py | grep -nE "version|banner|icon"
git show origin/<versi>:<modul>/__manifest__.py | grep -c "banner.png"   # harus 0

# 4. hash akhir untuk log
git rev-parse --short origin/staging/<versi> origin/<versi>
```

Lalu catat di tabel rujukan log: baris `Repo × Versi` dengan `Staging: DONE/SKIP + hash lama→baru` dan `Origin: DONE/SKIP + hash lama→baru`. Untuk SKIP, tulis alasannya ("sudah bersih sejak sesi …", "staging=origin sudah identik").

---

## Urutan eksekusi banyak repo [BARU]

Cleaning dan publish dilakukan **per repo, berurutan**. Paralel hanya untuk pekerjaan read-only.

| Fase | Mode | Isi |
|---|---|---|
| 1. Audit awal | Paralel (read-only) | Cek `git ls-tree`, manifest, dan README semua repo × versi. Hasilnya tabel DONE/SKIP sebelum mengubah apa pun. |
| 2. Eksekusi | **Berurutan** | Satu repo, semua versinya, sampai Langkah 6, lalu repo berikutnya. Jangan campur per-repo dan per-versi dalam satu putaran. |
| 3. Verifikasi akhir | Paralel (read-only) | Fetch fresh semua repo, `diff origin/staging/X origin/X`, cek sisa file terlarang dan manifest di `origin/[versi]`. |

Alasan tidak paralel saat eksekusi:
- Struktur tiap repo berbeda (`LICENSE.txt`, `CLAUDE.md` nyempil di modul, README placeholder), jadi perlu diperiksa satu per satu.
- Insiden `pos_margin_sale` berawal dari satu langkah (reset sebelum merge) yang terlewat. Banyak repo sekaligus membuat kelalaian seperti ini sulit terlihat.
- Token push dipasang per repo. Push paralel menyulitkan melacak mana yang gagal.
- "Everything up-to-date" yang tak terduga harus ditindaklanjuti per kasus, bukan tenggelam di output paralel.
- Hash `lama→baru` untuk log lebih akurat kalau satu repo selesai dulu.

Repo dengan banyak modul (`french_business_directory`, `pos_margin_sale`): tetap satu eksekusi per repo, modul di dalamnya diproses satu per satu.

---

## Cara membaca status (definisi dari log)

| Status | Arti |
|---|---|
| DONE | Ada perubahan, ada commit/push baru. |
| SKIP | Sudah dicek satu per satu, tidak ada yang perlu diubah, tidak ada commit baru. |
| Belum dikerjakan | Ditunda sengaja (contoh: `Doodex_growth_suite`), bukan terlewat. |

## Ringkasan pelajaran (anti-pengulangan)

1. Reset lokal ke origin sebelum merge. Itu penyebab insiden `pos_margin_sale`.
2. "Everything up-to-date" yang tidak terduga adalah alarm, bukan kabar baik.
3. Periksa keberadaan file nyata sebelum menulis `images` di manifest.
4. Sisa file terlarang bisa ada **di dalam folder modul**, bukan hanya root. Cek semua level.
5. Verifikasi di `origin/[versi]`, karena itu yang dilihat store.
6. Noise CRLF/LF jangan ikut di-commit.
7. Jangan tulis token ke log atau chat.
8. Bump version hanya di `migration/[versi]`, sebelum cleaning. Staging dan publish hanya mewarisi.
9. Eksekusi per repo berurutan; paralel hanya untuk audit dan verifikasi (read-only).

## Contoh pemakaian untuk repo ini (advanced_sales_analysis 20.0) [BARU]

Catatan: log asli belum mencakup 20.0 dan repo ini baru selesai migrasi. Kalau `migration/20.0` mau dipublish:

1. Cleaning: `CLAUDE.md` dan `doc-dev/` ada di root repo ini, dan `.claude/` juga ada (saat ini `.claude/skills/` masih untracked). Semuanya harus hilang dari `staging/20.0`.
2. Manifest 20.0 sudah memuat `images` (ditambah saat migrasi). Verifikasi nama file vs isi `static/description/`.
3. Cek README modul ("Odoo version: 20.0").
4. Folder `tests/` modul dihapus di staging, padahal itu bukti test 43 test migrasi. Aman karena tetap ada di `migration/20.0`.
5. Lanjutkan Langkah 4 → 6. `git push` tetap dilakukan manual oleh dev (aturan CLAUDE.md repo ini: AI tidak boleh push).
