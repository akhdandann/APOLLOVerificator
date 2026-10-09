# Mock-Up Validasi dan Verifikasi Data Polis

Aplikasi simulasi berbasis Streamlit untuk memvalidasi dan memverifikasi data polis asuransi konvensional secara massal (*bulk entry*). Data polis yang diunggah diperiksa terhadap database identitas dummy, kemudian dikelompokkan secara otomatis menjadi data valid, data tidak valid, dan data yang memerlukan inspeksi.

> **Catatan:** Aplikasi ini merupakan mock-up. Seluruh database menggunakan data dummy dan tidak terhubung dengan APOLO, Dukcapil, DJP, maupun Imigrasi. Belum ada skenario untuk bagian user tertentu seperti user mana yang punya hak akses tertentu, sehingga disini menggunakan POV user dengan hak akses tertinggi.

---

## Daftar Isi

1. [Fitur Utama](#fitur-utama)
2. [Alur Kerja](#alur-kerja)
3. [Aturan Validasi](#aturan-validasi)
4. [Aturan Gelar Haji](#aturan-gelar-haji)
5. [Aturan Flag Inspeksi](#aturan-flag-inspeksi)
6. [Struktur Proyek](#struktur-proyek)
7. [Format Database](#format-database)
8. [Format Berkas Unggahan](#format-berkas-unggahan)
9. [Instalasi dan Menjalankan Aplikasi](#instalasi-dan-menjalankan-aplikasi)
10. [Skenario Pengujian](#skenario-pengujian)
11. [Catatan Penggunaan](#catatan-penggunaan)

---

## Fitur Utama

| Fitur | Keterangan |
|---|---|
| Unggah massal | Mendukung berkas `.xlsx`, `.xls`, dan `.csv` dengan deteksi *encoding* otomatis |
| Validasi berlapis | Format identitas, struktur NIK, kewajaran tanggal polis, kecocokan dengan database, dan duplikasi |
| Empat jenis identitas | NIK, NPWP, Paspor, dan KITAS |
| Pengecekan gelar Haji | Perbedaan gelar H. atau Hj. antara database dan data polis ditangani secara khusus |
| Peninjauan manual | Data yang memerlukan inspeksi dapat diterima atau ditolak, baik satu per satu maupun sekaligus |
| Penyimpanan otomatis | Data yang tidak valid sejak awal langsung disimpan ke database tidak valid |
| Pencegahan duplikasi | Data yang sama persis (selain `timestamp`) tidak dicatat dua kali |
| Unduh hasil | Hasil validasi dapat diunduh dalam format CSV |

---

## Alur Kerja

```
Unggah berkas
     |
     v
Jalankan Validasi Massal
     |
     |--> Data Valid
     |        |
     |        +--> Tombol "Simpan Data Valid ke Database"
     |                  |
     |                  v
     |             database/data_valid.xlsx
     |
     |--> Data Tidak Valid
     |        |
     |        +--> Tersimpan otomatis
     |                  |
     |                  v
     |             database/data_tidak_valid.xlsx
     |
     +--> Data Perlu Inspeksi
              |
              |--> Terima / Terima Semua --> database/data_valid.xlsx
              +--> Tolak  / Tolak Semua  --> database/data_tidak_valid.xlsx
```

Urutan tampilan hasil pada aplikasi:

| Urutan | Bagian | Keterangan |
|---|---|---|
| 1 | Data Valid | Lolos seluruh pemeriksaan tanpa flag |
| 2 | Data Tidak Valid | Gagal pemeriksaan, disertai alasan dan bukti |
| 3 | Data Perlu Inspeksi | Lolos pemeriksaan, tetapi memerlukan peninjauan manual |

---

## Aturan Validasi

### 1. Kelengkapan Data

Kolom berikut wajib diisi: `nomor_polis`, `nama_pemegang`, `nomor_identitas`, `tanggal_mulai`, `tanggal_selesai`, `tanggal_lahir`, dan `lokasi`.

### 2. Format Nomor Identitas

| Jenis | Aturan |
|---|---|
| NIK | 15 atau 16 digit angka |
| NPWP | 8, 15, atau 16 digit angka |
| PASPOR | 7 sampai 9 karakter alfanumerik |
| KITAS | 11 digit angka |

### 3. Struktur NIK

Pemeriksaan ini hanya berlaku untuk jenis identitas NIK.

- NIK harus terdiri atas 16 digit angka.
- Kode wilayah (4 digit pertama) harus terdaftar pada `kode_wilayah.xlsx` apabila berkas tersebut tersedia.
- Tanggal lahir pada NIK harus sesuai dengan `tanggal_lahir` yang dilaporkan. Nilai tanggal di atas 40 menandakan jenis kelamin perempuan.
- Jenis kelamin pada NIK harus sesuai dengan `jenis_kelamin` yang dilaporkan.

### 4. Kewajaran Tanggal Polis

| Aturan | Hasil jika dilanggar |
|---|---|
| Tanggal Selesai harus setelah Tanggal Mulai | Tidak valid |
| Tanggal Mulai maksimal 1 tahun ke depan | Tidak valid |
| Tanggal tidak boleh sebelum tahun 1950 | Tidak valid |

### 5. Kecocokan dengan Database

| Jenis | Atribut yang dibandingkan |
|---|---|
| NIK | Nama, tanggal lahir, jenis kelamin, dan lokasi |
| NPWP | Nama |
| PASPOR | Nama |
| KITAS | Nama |

Perbandingan nama dilakukan tanpa gelar (misalnya `Dr.`, `S.H.`, `M.Si.`, `H.`, dan `Hj.`) serta tanpa memperhatikan huruf besar atau kecil.

### 6. Duplikasi NIK

NIK yang sudah tercatat pada database polis dengan nama yang berbeda dinyatakan tidak valid.

---

## Aturan Gelar Haji

Pemeriksaan ini hanya dijalankan apabila nama dasar (tanpa gelar) pada database dan data polis sudah sama.

| Nama pada Database | Nama pada Data Polis | Hasil |
|---|---|---|
| H. Hendra | H. Hendra | Valid, perlu inspeksi |
| Hendra | H. Hendra | Tidak valid |
| H. Hendra | Hendra | Valid, perlu inspeksi |
| Hendra | Hendra | Valid |

Gelar yang dikenali: `H`, `Hj`, `Haji`, dan `Hajjah`.

---

## Aturan Flag Inspeksi

Data tetap dinyatakan valid, tetapi ditandai perlu inspeksi apabila memenuhi salah satu kondisi berikut.

| Kondisi | Keterangan |
|---|---|
| Masa pertanggungan sangat panjang | Lebih dari 30 tahun |
| Masa pertanggungan sangat pendek | Kurang dari 30 hari |
| Tanggal Selesai sangat jauh | Lebih dari 50 tahun dari tanggal saat ini |
| Gelar Haji | Sesuai tabel pada bagian [Aturan Gelar Haji](#aturan-gelar-haji) |

Setiap kartu inspeksi hanya menampilkan alasan dan bukti dari atribut terkait. Untuk flag nama, bukti menampilkan nama lengkap beserta gelarnya.

---

## Struktur Proyek

```
.
├── app.py                         # Aplikasi utama Streamlit
├── requirements.txt               # Daftar dependensi
├── README.md
└── database/
    ├── db_nik.xlsx                # Database NIK dummy
    ├── db_npwp.xlsx               # Database NPWP dummy
    ├── db_paspor.xlsx             # Database Paspor dummy
    ├── db_kitas.xlsx              # Database KITAS dummy
    ├── kode_wilayah.xlsx          # (Opsional) Referensi kode wilayah
    ├── data_valid.xlsx            # Dibuat otomatis: data polis valid
    └── data_tidak_valid.xlsx      # Dibuat otomatis: data polis tidak valid
```

---

## Format Database

Nama kolom tidak peka huruf besar atau kecil. Spasi dan titik pada nama kolom otomatis diubah menjadi garis bawah.

### Database Referensi

| Berkas | Kolom |
|---|---|
| `db_nik.xlsx` | `nik`, `nama`, `tanggal_lahir`, `jenis_kelamin`, `lokasi` |
| `db_npwp.xlsx` | `npwp`, `nama` |
| `db_paspor.xlsx` | `paspor`, `nama` |
| `db_kitas.xlsx` | `kitas`, `nama` |
| `kode_wilayah.xlsx` | `kode` |

### Database Keluaran

| Berkas | Isi | Kolom Tambahan |
|---|---|---|
| `data_valid.xlsx` | Data polis valid, termasuk yang diterima setelah inspeksi | `flag_inspeksi`, `alasan_flag`, `timestamp` |
| `data_tidak_valid.xlsx` | Data tidak valid otomatis dan data yang ditolak setelah inspeksi | `alasan`, `bukti`, `status`, `timestamp` |

Nilai kolom `status` pada database tidak valid:

| Status | Arti |
|---|---|
| `TIDAK VALID (OTOMATIS)` | Gagal validasi sejak awal |
| `DITOLAK SETELAH INSPEKSI` | Ditolak secara manual pada tahap inspeksi |

### Pencegahan Duplikasi

Sebelum menyimpan, aplikasi membandingkan data baru dengan seluruh data yang sudah ada. Apabila semua atribut sama (kecuali `timestamp`), data tidak dicatat dan aplikasi menampilkan pesan bahwa data yang sama sudah ada di database. Khusus database tidak valid, kolom `baris` tidak ikut dibandingkan karena hanya menunjukkan posisi baris pada berkas unggahan.

---

## Format Berkas Unggahan

Template dapat diunduh langsung dari aplikasi melalui tombol **Unduh Template Excel (CSV)**.

| Kolom | Contoh | Wajib |
|---|---|---|
| `nomor_polis` | `POL-2026-0001` | Ya |
| `nama_pemegang` | `Hendra` | Ya |
| `jenis_identitas` | `NIK` | Ya |
| `nomor_identitas` | `3201981802850009` | Ya |
| `tanggal_mulai` | `2025/01/05` | Ya |
| `tanggal_selesai` | `2025/01/31` | Ya |
| `tanggal_lahir` | `1985/02/18` | Ya |
| `jenis_kelamin` | `L - Laki-Laki` | Ya |
| `lokasi` | `3201 - KAB. BOGOR, PROVINSI JAWA BARAT` | Ya |
| `lini_usaha` | `1027 - Anuitas Dana Pensiun` | Tidak |
| `cara_bayar` | `101 - Reguler - Bulanan` | Tidak |
| `jumlah_premi` | `2000` | Tidak |
| `uang_pertanggungan` | `1200` | Tidak |
| `cadangan_premi` | `5000` | Tidak |
| `capybmp` | `3450` | Tidak |
| `jumlah_tertanggung` | `5` | Tidak |

Format tanggal yang dikenali meliputi `YYYY/MM/DD`, `YYYY-MM-DD`, `YYYYMMDD`, dan format tanggal umum lainnya. Seluruhnya dinormalisasi menjadi `YYYY/MM/DD`.

---

## Instalasi dan Menjalankan Aplikasi

### Prasyarat

- Python 3.9 atau lebih baru
- Streamlit 1.39 atau lebih baru (diperlukan agar warna tombol Terima dan Tolak tampil dengan benar)

### 1. Clone repositori

```bash
git clone https://github.com/<username>/<nama-repositori>.git
cd <nama-repositori>
```

### 2. Buat virtual environment (opsional)

```bash
python -m venv venv
```

Aktifkan virtual environment:

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Pasang dependensi

Buat berkas `requirements.txt` dengan isi berikut:

```text
streamlit>=1.39
pandas
openpyxl
```

Kemudian jalankan:

```bash
pip install -r requirements.txt
```

### 4. Siapkan database dummy

Letakkan berkas `db_nik.xlsx`, `db_npwp.xlsx`, `db_paspor.xlsx`, dan `db_kitas.xlsx` pada folder `database/` sesuai [format database](#format-database).

### 5. Jalankan aplikasi

```bash
streamlit run app.py
```

Aplikasi dapat diakses melalui `http://localhost:8501`.

---

## Skenario Pengujian

### Aturan Gelar Haji

Pengujian dilakukan dengan NIK yang sama, tetapi nama berbeda pada database dan data polis.

| Skenario | Database NIK | Data Polis | Hasil yang Diharapkan |
|---|---|---|---|
| 1 | H. Hendra | H. Hendra | Muncul pada Data Perlu Inspeksi |
| 2 | Hendra | H. Hendra | Muncul pada Data Tidak Valid dan tersimpan otomatis |
| 3 | Hendra | Hendra | Muncul pada Data Valid |

### Pencegahan Duplikasi

1. Unggah berkas, jalankan validasi, lalu simpan data valid.
2. Unggah berkas yang sama dan jalankan validasi kembali.
3. Tekan tombol **Simpan Data Valid ke Database**.
4. Aplikasi menampilkan peringatan bahwa data tidak dicatat karena data yang sama sudah ada.

---

## Catatan Penggunaan

- Aplikasi menggunakan data dummy dan hanya ditujukan untuk keperluan simulasi.
- Berkas Excel pada folder `database/` harus dalam keadaan tertutup saat aplikasi menyimpan data. Apabila terbuka di aplikasi lain, penyimpanan gagal dan aplikasi menampilkan pesan kesalahan.
- Pastikan folder `database/` yang berisi data asli atau sensitif tidak ikut diunggah ke repositori publik. Tambahkan folder tersebut ke `.gitignore` apabila diperlukan.
