# Mock-Up Validasi dan Verifikasi Data Polis

Aplikasi simulasi untuk validasi dan verifikasi data polis asuransi konvensional. Aplikasi ini dikembangkan sebagai bagian dari Laporan On The Job Training (OJT) di Departemen Aktuaria, Otoritas Jasa Keuangan (OJK).

> **Catatan:** Aplikasi ini menggunakan **data dummy** dan **tidak terhubung** dengan APOLO, Dukcapil, DJP, maupun Imigrasi. Seluruh data yang digunakan bersifat fiktif dan hanya untuk keperluan demonstrasi.

---

## Daftar Isi

- [Latar Belakang](#latar-belakang)
- [Fitur](#fitur)

---

## Latar Belakang

Data polis merupakan salah satu sumber informasi yang digunakan OJK untuk mendukung pengawasan, analisis, dan pemantauan industri perasuransian. Namun, kualitas data yang diterima masih perlu ditingkatkan, terutama pada data identitas nasabah seperti NIK, NPWP, dan nomor paspor.

Aplikasi ini dikembangkan untuk:
1. Memvalidasi struktur NIK secara mandiri tanpa akses Dukcapil.
2. Memvalidasi format NPWP, Paspor, dan KITAS.
3. Memeriksa konsistensi data dengan database dummy.
4. Mendeteksi duplikat NIK.
5. Menyimpan data valid ke database.

---

## Fitur

### 1. Validasi Struktur NIK (Tanpa Dukcapil)

- **Format**: Memastikan NIK terdiri atas 16 digit angka.
- **Kode Wilayah**: Memvalidasi 6 digit pertama NIK terhadap referensi kode wilayah Kemendagri.
- **Tanggal Lahir**: Mengekstrak tanggal lahir dari digit 7–12 NIK dan membandingkannya dengan data yang dilaporkan.
- **Jenis Kelamin**: Mendeteksi jenis kelamin dari NIK (tanggal > 40 = perempuan).
- **Nomor Urut**: 4 digit terakhir sebagai nomor urut.

### 2. Validasi Format Identitas Lain

- **NPWP**: 8, 15, atau 16 digit angka.
- **Paspor**: 1–2 huruf kapital diikuti 7 digit angka.
- **KITAS**: 11 digit angka.

### 3. Validasi Konsistensi

- **Nama**: Dibandingkan setelah normalisasi (gelar dihapus).
- **Tanggal Lahir**: Dibandingkan dengan data di database.
- **Jenis Kelamin**: Dibandingkan dengan data di database.
- **Lokasi**: Dibandingkan dengan data di database.

### 4. Deteksi Duplikat

- Mendeteksi NIK yang sudah terdaftar dengan nama berbeda di database polis.

### 5. Bulk Entry

- Unggah berkas Excel/CSV berisi banyak data polis.
- Validasi setiap baris secara otomatis.
- Menampilkan baris yang bermasalah dengan alasan dan bukti.

### 6. Penyimpanan Database

- Data valid disimpan ke `database/data_valid.xlsx`.
- Duplikat tidak disimpan.

### 7. Multi-Encoding CSV

- Mendukung UTF-8, UTF-8-SIG, Windows-1252, ISO-8859-1, dan Latin-1.
