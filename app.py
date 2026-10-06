import streamlit as st
import pandas as pd
import re
import os
import traceback
import unicodedata
from datetime import datetime


# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Mock-Up Validasi Data Polis",
    page_icon=None,
    layout="wide",
)


# ============================================================
# FUNGSI BANTU
# ============================================================
def normalisasi_tanggal(tanggal) -> str:
    """Mengubah format tanggal apa pun menjadi YYYY/MM/DD."""
    if tanggal is None:
        return ""
    if isinstance(tanggal, str) and not tanggal.strip():
        return ""
    try:
        s = str(tanggal).strip()
        if re.match(r"^\d{8}$", s):
            dt = datetime.strptime(s, "%Y%m%d")
            return dt.strftime("%Y/%m/%d")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.strftime("%Y/%m/%d")
        if re.match(r"^\d{4}/\d{2}/\d{2}$", s):
            dt = datetime.strptime(s, "%Y/%m/%d")
            return dt.strftime("%Y/%m/%d")
        dt = pd.to_datetime(s, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.strftime("%Y/%m/%d")
    except Exception:
        return ""


def validasi_tanggal_polis(tanggal_mulai: str, tanggal_selesai: str):
    """
    Memvalidasi kewajaran tanggal polis.
    Mengembalikan (valid: bool, pesan: str, flag: bool, alasan_flag: str).
    """
    hari_ini = datetime.now()

    if not tanggal_mulai:
        return False, "Tanggal Mulai Polis kosong.", False, ""
    if not tanggal_selesai:
        return False, "Tanggal Selesai Polis kosong.", False, ""

    try:
        tgl_mulai = datetime.strptime(tanggal_mulai, "%Y/%m/%d")
    except Exception:
        return False, f"Format Tanggal Mulai tidak valid: '{tanggal_mulai}'.", False, ""

    try:
        tgl_selesai = datetime.strptime(tanggal_selesai, "%Y/%m/%d")
    except Exception:
        return False, f"Format Tanggal Selesai tidak valid: '{tanggal_selesai}'.", False, ""

    if tgl_selesai <= tgl_mulai:
        return (
            False,
            f"Tanggal Selesai ({tanggal_selesai}) harus setelah Tanggal Mulai ({tanggal_mulai}).",
            False,
            "",
        )

    batas_depan = hari_ini.replace(year=hari_ini.year + 1)
    if tgl_mulai > batas_depan:
        return (
            False,
            f"Tanggal Mulai ({tanggal_mulai}) terlalu jauh di masa depan (maksimal 1 tahun).",
            False,
            "",
        )

    if tgl_mulai.year < 1950 or tgl_selesai.year < 1950:
        return False, "Tanggal polis tidak boleh sebelum tahun 1950.", False, ""

    selisih_hari = (tgl_selesai - tgl_mulai).days
    flag = False
    alasan_flag = []

    if selisih_hari > 30 * 365:
        flag = True
        alasan_flag.append(
            f"Masa pertanggungan sangat panjang: {selisih_hari} hari "
            f"(± {selisih_hari // 365} tahun). Perlu inspeksi."
        )

    if selisih_hari < 30:
        flag = True
        alasan_flag.append(
            f"Masa pertanggungan sangat pendek: {selisih_hari} hari. Perlu inspeksi."
        )

    if tgl_selesai.year > hari_ini.year + 50:
        flag = True
        alasan_flag.append(
            f"Tanggal Selesai ({tanggal_selesai}) sangat jauh di masa depan. Perlu inspeksi."
        )

    pesan = "Tanggal polis valid." if not flag else "Tanggal polis valid, tetapi perlu inspeksi."
    return True, pesan, flag, " | ".join(alasan_flag)


def bersihkan_nik(nik) -> str:
    if nik is None:
        return ""
    s = str(nik).strip()
    if re.match(r"^\d+[,.]?\d*[eE][+-]?\d+$", s):
        try:
            s = f"{float(s.replace(',', '.')):.0f}"
        except Exception:
            pass
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"\D", "", s)
    return s


def normalisasi_nama(nama: str) -> str:
    if not nama:
        return ""
    nama = unicodedata.normalize("NFKC", str(nama))
    nama = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", nama)
    nama = re.sub(r"\s+", " ", nama).strip()
    nama = nama.lower()
    nama = re.sub(r"[,;]", " ", nama)

    pola_gelar = [
        r"\bs\.\s*[a-z]{1,3}\.?\b",
        r"\bm\.\s*[a-z]{1,3}\.?\b",
        r"\ba\.md\.\s*[a-z]{1,3}\.?\b",
        r"\bd\s*[34]\b",
        r"\bprof\.?\b",
        r"\bdr[sg]?\.?\b",
        r"\bir\.?\b",
        r"\bb\.\s*[a-z]{1,3}\.?\b",
        r"\bph\.?\s*d\.?\b",
        r"\bm\.?\s*d\.?\b",
        r"\bh\.?\b",
        r"\bhj\.?\b",
        r"\bk\.?\s*h\.?\b",
        r"\bust\.?\b",
        r"\bpdt\.?\b",
        r"\br\.?\s*a\.?\b",
        r"\br\.?\s*m\.?\b",
        r"\bk\.?\s*r\.?\s*t\.?\b",
        r"\btb\.?\b",
    ]

    sebelumnya = None
    while sebelumnya != nama:
        sebelumnya = nama
        for pola in pola_gelar:
            nama = re.sub(pola, " ", nama)

    nama = re.sub(r"[.,]", " ", nama)
    nama = re.sub(r"\s+", " ", nama).strip()

    token = nama.split()
    return " ".join(token)


def perbaiki_format_nama(nama: str) -> str:
    if not nama:
        return ""
    nama_bersih = normalisasi_nama(nama)
    singkatan_badan_usaha = {
        "PT", "CV", "TB", "UD", "PD", "KOPERASI", "YAYASAN",
        "FIRMA", "FA", "PTA", "PERSERO", "PERUM", "BUMN",
        "BUMD", "BUMDES", "PTNV", "PMA", "PMDN",
    }
    token = nama_bersih.split()
    hasil = []
    for t in token:
        t_bersih = t.rstrip(".")
        if t_bersih.upper() in singkatan_badan_usaha:
            hasil.append(t_bersih.upper())
        else:
            hasil.append(t_bersih.capitalize())
    return " ".join(hasil)


# ============================================================
# VALIDASI STRUKTUR NIK (TANPA DUKCAPIL)
# ============================================================
def muat_kode_wilayah():
    path = "database/kode_wilayah.xlsx"
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_excel(path, dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception:
        return None


kode_wilayah = muat_kode_wilayah()


def validasi_struktur_nik(nik: str, tanggal_lahir: str = "", jenis_kelamin: str = ""):
    if not nik:
        return False, "NIK kosong."

    nik = bersihkan_nik(nik)

    if not re.match(r"^\d{16}$", nik):
        return False, f"NIK harus terdiri atas 16 digit angka. Ditemukan: '{nik}' ({len(nik)} digit)."

    kode_kab = nik[0:4]
    if kode_wilayah is not None:
        baris = kode_wilayah[kode_wilayah["kode"] == kode_kab]
        if baris.empty:
            return False, f"Kode wilayah '{kode_kab}' tidak terdaftar pada referensi Kemendagri."

    tgl_nik = int(nik[6:8])
    bln_nik = int(nik[8:10])
    thn_nik = int(nik[10:12])

    if tgl_nik > 40:
        tgl_asli = tgl_nik - 40
        jk_nik = "P"
    else:
        tgl_asli = tgl_nik
        jk_nik = "L"

    if not (1 <= tgl_asli <= 31):
        return False, f"Tanggal lahir pada NIK tidak valid: {tgl_asli}."
    if not (1 <= bln_nik <= 12):
        return False, f"Bulan lahir pada NIK tidak valid: {bln_nik}."

    if tanggal_lahir:
        try:
            bagian = tanggal_lahir.split("/")
            thn_input = int(bagian[0]) % 100
            bln_input = int(bagian[1])
            tgl_input = int(bagian[2])
            if (thn_nik, bln_nik, tgl_asli) != (thn_input, bln_input, tgl_input):
                return False, (
                    f"Tanggal lahir pada NIK ({tgl_asli:02d}/{bln_nik:02d}/{thn_nik:02d}) "
                    f"tidak sesuai dengan yang dilaporkan "
                    f"({tgl_input:02d}/{bln_input:02d}/{thn_input:02d})."
                )
        except Exception:
            return False, "Format tanggal lahir tidak dikenali."

    if jenis_kelamin:
        jk_input = str(jenis_kelamin).strip()[0].upper()
        if jk_input != jk_nik:
            return False, (
                f"Jenis kelamin pada NIK ({jk_nik}) tidak sesuai dengan yang "
                f"dilaporkan ({jk_input})."
            )

    return True, "Struktur NIK valid."


# ============================================================
# DUPLIKAT NIK
# ============================================================
def cek_duplikat_nik(nomor_identitas: str, nama: str):
    if not nomor_identitas or not nama:
        return False, ""
    nama_norm = normalisasi_nama(nama)
    nomor_bersih = bersihkan_nik(nomor_identitas)
    baris = db_nik[db_nik["nik"] == nomor_bersih]
    if baris.empty:
        return False, ""
    nama_db = baris.iloc[0].get("nama", "")
    nama_db_norm = normalisasi_nama(nama_db)
    if nama_db_norm == nama_norm:
        return False, ""
    return True, f"NIK sudah terdaftar dengan nama '{nama_db}' di database kependudukan."


def cek_duplikat_nik_di_database_polis(nomor_identitas: str, nama: str):
    if not nomor_identitas or not nama:
        return False, ""
    path = "database/data_valid.xlsx"
    if not os.path.exists(path):
        return False, ""
    try:
        df = pd.read_excel(path, dtype=str)
    except Exception:
        return False, ""
    if "nomor_identitas" not in df.columns or "nama_pemegang" not in df.columns:
        return False, ""
    nomor_bersih = bersihkan_nik(nomor_identitas)
    baris = df[df["nomor_identitas"].apply(bersihkan_nik) == nomor_bersih]
    if baris.empty:
        return False, ""
    nama_norm = normalisasi_nama(nama)
    for _, row in baris.iterrows():
        nama_lama = row.get("nama_pemegang", "")
        if normalisasi_nama(nama_lama) == nama_norm:
            return False, ""
    nama_lama_pertama = baris.iloc[0].get("nama_pemegang", "")
    return True, f"NIK sudah terdaftar dengan nama '{nama_lama_pertama}' pada database polis."


# ============================================================
# PEMUATAN DATABASE DUMMY
# ============================================================
def muat_database():
    try:
        db_nik = pd.read_excel("database/db_nik.xlsx", dtype=str)
        db_npwp = pd.read_excel("database/db_npwp.xlsx", dtype=str)
        db_paspor = pd.read_excel("database/db_paspor.xlsx", dtype=str)
        db_kitas = pd.read_excel("database/db_kitas.xlsx", dtype=str)
    except FileNotFoundError as e:
        st.error(f"Berkas database tidak ditemukan: {e}")
        st.stop()
    except PermissionError as e:
        st.error(f"Berkas database sedang dibuka di aplikasi lain: {e}")
        st.info("Silakan tutup berkas Excel, lalu muat ulang halaman ini.")
        st.stop()
    except Exception as e:
        st.error(f"Gagal memuat database: {type(e).__name__} — {e}")
        st.code(traceback.format_exc())
        st.stop()

    for df in (db_nik, db_npwp, db_paspor, db_kitas):
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[.\s]+", "_", regex=True)
        )

    if "tanggal_lahir" in db_nik.columns:
        db_nik["tanggal_lahir"] = db_nik["tanggal_lahir"].apply(normalisasi_tanggal)

    for df, kolom in [
        (db_nik, "nik"),
        (db_npwp, "npwp"),
        (db_paspor, "paspor"),
        (db_kitas, "kitas"),
    ]:
        if kolom in df.columns:
            df[kolom] = df[kolom].apply(bersihkan_nik)

    return db_nik, db_npwp, db_paspor, db_kitas


db_nik, db_npwp, db_paspor, db_kitas = muat_database()


# ============================================================
# FUNGSI BACA BERKAS (MULTI-ENCODING)
# ============================================================
def baca_berkas_unggahan(berkas):
    if berkas.name.lower().endswith(".csv"):
        encodings = ["utf-8", "utf-8-sig", "windows-1252", "iso-8859-1", "latin1"]
        for enc in encodings:
            try:
                berkas.seek(0)
                df = pd.read_csv(berkas, dtype=str, encoding=enc)
                return df, enc
            except (UnicodeDecodeError, Exception):
                continue
        return None, "Encoding CSV tidak dikenali. Silakan konversi ke UTF-8 atau simpan sebagai XLSX."
    else:
        try:
            berkas.seek(0)
            df = pd.read_excel(berkas, dtype=str)
            return df, "xlsx"
        except Exception as e:
            return None, f"Gagal membaca Excel: {type(e).__name__} — {e}"


# ============================================================
# FUNGSI VALIDASI FORMAT
# ============================================================
def validasi_format(jenis_identitas: str, nomor: str):
    pola = {
        "NIK":    (r"^\d{15,16}$", "NIK harus terdiri atas 15 atau 16 digit angka."),
        "NPWP":   (r"^\d{8}$|^\d{15,16}$", "NPWP harus terdiri atas 8, 15, atau 16 digit angka."),
        "PASPOR": (r"^[A-Z0-9]{7,9}$", "Nomor paspor harus terdiri atas 7 sampai 9 digit alfanumerik."),
        "KITAS":  (r"^\d{11}$", "KITAS harus terdiri atas 11 digit angka."),
    }
    if jenis_identitas not in pola:
        return False, f"Jenis identitas '{jenis_identitas}' tidak dikenali."
    regex, pesan = pola[jenis_identitas]
    if re.match(regex, nomor.strip()):
        return True, "Format sesuai dengan ketentuan."
    return False, pesan


def cek_database(jenis_identitas: str, nomor: str):
    nomor_bersih = bersihkan_nik(nomor)
    if jenis_identitas == "NIK":
        baris = db_nik[db_nik["nik"] == nomor_bersih]
    elif jenis_identitas == "NPWP":
        baris = db_npwp[db_npwp["npwp"] == nomor_bersih]
    elif jenis_identitas == "PASPOR":
        baris = db_paspor[db_paspor["paspor"] == nomor_bersih]
    elif jenis_identitas == "KITAS":
        baris = db_kitas[db_kitas["kitas"] == nomor_bersih]
    else:
        return False, None
    if baris.empty:
        return False, None
    return True, baris.iloc[0].to_dict()


def cek_konsistensi(jenis_identitas: str, data_db: dict, data_input: dict):
    kesalahan = []
    if jenis_identitas == "NIK":
        nama_db = data_db.get("nama", "").strip()
        nama_input = data_input["nama"].strip()
        if normalisasi_nama(nama_db) != normalisasi_nama(nama_input):
            kesalahan.append({
                "alasan": "Nama pemegang polis tidak sesuai dengan data pada database kependudukan.",
                "bukti": f"Nama pada database: '{nama_db}'",
            })
        tgl_db = data_db.get("tanggal_lahir", "")
        tgl_input = data_input["tanggal_lahir"]
        if tgl_db and tgl_db != tgl_input:
            kesalahan.append({
                "alasan": "Tanggal lahir pemegang polis tidak sesuai dengan data pada database kependudukan.",
                "bukti": f"Tanggal lahir pada database: '{tgl_db}'",
            })
        jk_db = data_db.get("jenis_kelamin", "").strip()
        jk_input = data_input["jenis_kelamin"].strip()
        if jk_db and jk_db[0].upper() != jk_input[0].upper():
            kesalahan.append({
                "alasan": "Jenis kelamin pemegang polis tidak sesuai dengan data pada database kependudukan.",
                "bukti": f"Jenis kelamin pada database: '{jk_db}'",
            })
        lok_db = data_db.get("lokasi", "").strip()
        lok_input = data_input["lokasi"].strip()
        if lok_db and lok_db.lower() != lok_input.lower():
            kesalahan.append({
                "alasan": "Lokasi pemegang polis tidak sesuai dengan data pada database kependudukan.",
                "bukti": f"Lokasi pada database: '{lok_db}'",
            })
    elif jenis_identitas == "NPWP":
        nama_db = data_db.get("nama", "").strip()
        nama_input = data_input["nama"].strip()
        if normalisasi_nama(nama_db) != normalisasi_nama(nama_input):
            kesalahan.append({
                "alasan": "Nama pemegang polis tidak sesuai dengan data pada database perpajakan.",
                "bukti": f"Nama pada database: '{nama_db}'",
            })
    elif jenis_identitas == "PASPOR":
        nama_db = data_db.get("nama", "").strip()
        nama_input = data_input["nama"].strip()
        if normalisasi_nama(nama_db) != normalisasi_nama(nama_input):
            kesalahan.append({
                "alasan": "Nama pemegang polis tidak sesuai dengan data pada database keimigrasian.",
                "bukti": f"Nama pada database: '{nama_db}'",
            })
    elif jenis_identitas == "KITAS":
        nama_db = data_db.get("nama", "").strip()
        nama_input = data_input["nama"].strip()
        if normalisasi_nama(nama_db) != normalisasi_nama(nama_input):
            kesalahan.append({
                "alasan": "Nama pemegang polis tidak sesuai dengan data pada database keimigrasian.",
                "bukti": f"Nama pada database: '{nama_db}'",
            })
    return kesalahan


def simpan_ke_database_valid(record: dict):
    os.makedirs("database", exist_ok=True)
    path = "database/data_valid.xlsx"
    kolom_banding = [k for k in record.keys() if k != "timestamp"]
    df_baru = pd.DataFrame([record])
    if os.path.exists(path):
        df_lama = pd.read_excel(path, dtype=str)
        for kolom in kolom_banding:
            if kolom not in df_lama.columns:
                df_lama[kolom] = ""
        for _, baris_lama in df_lama.iterrows():
            sama = True
            for kolom in kolom_banding:
                nilai_lama = str(baris_lama.get(kolom, "")).strip()
                nilai_baru = str(record.get(kolom, "")).strip()
                if nilai_lama != nilai_baru:
                    sama = False
                    break
            if sama:
                return False
        df_gabung = pd.concat([df_lama, df_baru], ignore_index=True)
    else:
        df_gabung = df_baru
    df_gabung.to_excel(path, index=False)
    return True


# ============================================================
# BAGIAN ANTARMUKA
# ============================================================
st.title("Mock-Up Validasi dan Verifikasi Data Polis")
st.caption(
    "Aplikasi simulasi untuk validasi dan verifikasi data polis asuransi konvensional. "
    "Menggunakan data dummy dan tidak terhubung dengan APOLO, Dukcapil, DJP, maupun Imigrasi."
)

with st.sidebar:
    st.header("Informasi Database Dummy")
    st.metric("Total NIK", len(db_nik))
    st.metric("Total NPWP", len(db_npwp))
    st.metric("Total Paspor", len(db_paspor))
    st.metric("Total KITAS", len(db_kitas))
    if kode_wilayah is not None:
        st.metric("Total Kode Wilayah", len(kode_wilayah))
    with st.expander("Lihat Database NIK"):
        st.dataframe(db_nik, use_container_width=True)
    with st.expander("Lihat Database NPWP"):
        st.dataframe(db_npwp, use_container_width=True)
    with st.expander("Lihat Database Paspor"):
        st.dataframe(db_paspor, use_container_width=True)
    with st.expander("Lihat Database KITAS"):
        st.dataframe(db_kitas, use_container_width=True)


tab_bulk, tab_database = st.tabs(["Bulk Entry", "Database"])


# ============================================================
# TAB 1: BULK ENTRY
# ============================================================
with tab_bulk:
    st.subheader("Unggah Data Polis Secara Massal")
    st.caption(
        "Unggah berkas Excel berisi banyak data polis sekaligus. "
        "Sistem akan memvalidasi setiap baris dan menampilkan baris yang bermasalah."
    )

    template_data = pd.DataFrame([
        {
            "nomor_polis": "POL-2026-0001",
            "nama_pemegang": "Hendra",
            "jenis_identitas": "NIK",
            "nomor_identitas": "3201981802850009",
            "tanggal_mulai": "2025/01/05",
            "tanggal_selesai": "2025/01/31",
            "tanggal_lahir": "1985/02/18",
            "jenis_kelamin": "L - Laki-Laki",
            "lokasi": "3201 - KAB. BOGOR, PROVINSI JAWA BARAT",
            "lini_usaha": "1027 - Anuitas Dana Pensiun",
            "cara_bayar": "101 - Reguler - Bulanan",
            "jumlah_premi": "2000",
            "uang_pertanggungan": "1200",
            "cadangan_premi": "5000",
            "capybmp": "3450",
            "jumlah_tertanggung": "5",
        },
    ])

    template_csv = template_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Unduh Template Excel (CSV)",
        data=template_csv,
        file_name="template_bulk_entry.csv",
        mime="text/csv",
        key="bulk_unduh_template",
    )

    st.caption(
        "Template berisi contoh baris yang mencakup jenis identitas NIK. "
        "Silakan hapus baris contoh sebelum mengisi data sebenarnya."
    )

    berkas = st.file_uploader(
        label="Unggah Berkas Data Polis (Excel atau CSV)",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
        key="bulk_unggah_berkas",
    )

    if berkas is not None:
        df_unggah, info = baca_berkas_unggahan(berkas)
        if df_unggah is None:
            st.error(info)
            st.stop()
        if info != "xlsx":
            st.info(f"Berkas CSV dibaca dengan encoding: **{info}**")

        st.success(f"Berkas berhasil dimuat: {len(df_unggah)} baris data.")
        st.dataframe(df_unggah.head(10), use_container_width=True)

        if st.button(
            label="Jalankan Validasi Massal",
            use_container_width=True,
            key="bulk_tombol_validasi",
        ):
            hasil_valid = []
            hasil_tidak_valid = []
            progres = st.progress(0, text="Memulai validasi massal.")
            total = len(df_unggah)

            for i, baris in df_unggah.iterrows():
                progres.progress(
                    int((i + 1) / total * 100),
                    text=f"Memvalidasi baris {i + 1} dari {total}.",
                )

                kesalahan_alasan = []
                kesalahan_bukti = []

                nomor_polis = str(baris.get("nomor_polis", "")).strip()
                nama = str(baris.get("nama_pemegang", "")).strip()
                jenis_identitas = str(baris.get("jenis_identitas", "")).strip().upper()
                nomor_identitas = bersihkan_nik(baris.get("nomor_identitas", ""))
                tanggal_mulai = normalisasi_tanggal(baris.get("tanggal_mulai", ""))
                tanggal_selesai = normalisasi_tanggal(baris.get("tanggal_selesai", ""))
                tanggal_lahir = normalisasi_tanggal(baris.get("tanggal_lahir", ""))
                jenis_kelamin = str(baris.get("jenis_kelamin", "")).strip()
                lokasi = str(baris.get("lokasi", "")).strip()

                if not nomor_polis:
                    kesalahan_alasan.append("Nomor Polis kosong.")
                    kesalahan_bukti.append("Field nomor_polis tidak diisi.")
                if not nama:
                    kesalahan_alasan.append("Nama Pemegang Polis kosong.")
                    kesalahan_bukti.append("Field nama_pemegang tidak diisi.")
                if not nomor_identitas:
                    kesalahan_alasan.append("Nomor Identitas kosong.")
                    kesalahan_bukti.append("Field nomor_identitas tidak diisi.")
                if not tanggal_mulai:
                    kesalahan_alasan.append("Tanggal Mulai tidak valid.")
                    kesalahan_bukti.append(f"Nilai tanggal_mulai: '{baris.get('tanggal_mulai', '')}'")
                if not tanggal_selesai:
                    kesalahan_alasan.append("Tanggal Selesai tidak valid.")
                    kesalahan_bukti.append(f"Nilai tanggal_selesai: '{baris.get('tanggal_selesai', '')}'")
                if not tanggal_lahir:
                    kesalahan_alasan.append("Tanggal Lahir tidak valid.")
                    kesalahan_bukti.append(f"Nilai tanggal_lahir: '{baris.get('tanggal_lahir', '')}'")
                if not lokasi:
                    kesalahan_alasan.append("Lokasi kosong.")
                    kesalahan_bukti.append("Field lokasi tidak diisi.")

                # Validasi tanggal polis
                if tanggal_mulai and tanggal_selesai:
                    tanggal_valid, pesan_tanggal, flag_tanggal, alasan_flag = validasi_tanggal_polis(
                        tanggal_mulai, tanggal_selesai
                    )
                    if not tanggal_valid:
                        kesalahan_alasan.append("Tanggal polis tidak valid.")
                        kesalahan_bukti.append(pesan_tanggal)
                else:
                    flag_tanggal = False
                    alasan_flag = ""

                if nomor_identitas and jenis_identitas:
                    format_valid, pesan_format = validasi_format(jenis_identitas, nomor_identitas)
                    if not format_valid:
                        kesalahan_alasan.append(f"Format {jenis_identitas} tidak sesuai.")
                        kesalahan_bukti.append(f"{pesan_format} Nilai: '{nomor_identitas}'")

                if jenis_identitas == "NIK" and nomor_identitas:
                    struktur_valid, pesan_struktur = validasi_struktur_nik(
                        nomor_identitas, tanggal_lahir, jenis_kelamin
                    )
                    if not struktur_valid:
                        kesalahan_alasan.append("Struktur NIK tidak valid.")
                        kesalahan_bukti.append(pesan_struktur)

                data_db = None
                if nomor_identitas and jenis_identitas:
                    ditemukan, data_db = cek_database(jenis_identitas, nomor_identitas)
                    if not ditemukan:
                        kesalahan_alasan.append(
                            f"Nomor identitas tidak terdaftar pada database {jenis_identitas}."
                        )
                        kesalahan_bukti.append(
                            f"Nomor {jenis_identitas} '{nomor_identitas}' tidak ditemukan pada database."
                        )

                if data_db is not None:
                    data_input = {
                        "nama": nama,
                        "tanggal_lahir": tanggal_lahir,
                        "jenis_kelamin": jenis_kelamin,
                        "lokasi": lokasi,
                    }
                    kesalahan_konsistensi = cek_konsistensi(jenis_identitas, data_db, data_input)
                    for k in kesalahan_konsistensi:
                        kesalahan_alasan.append(k["alasan"])
                        kesalahan_bukti.append(k["bukti"])

                    if jenis_identitas == "NIK" and nomor_identitas:
                        is_duplikat, keterangan = cek_duplikat_nik_di_database_polis(nomor_identitas, nama)
                        if is_duplikat:
                            kesalahan_alasan.append("NIK sudah terdaftar dengan nama yang berbeda pada database polis.")
                            kesalahan_bukti.append(keterangan)

                if not kesalahan_alasan:
                    hasil_valid.append({
                        "nomor_polis": nomor_polis,
                        "nama_pemegang": perbaiki_format_nama(nama),
                        "jenis_identitas": jenis_identitas,
                        "nomor_identitas": nomor_identitas,
                        "tanggal_mulai": tanggal_mulai,
                        "tanggal_selesai": tanggal_selesai,
                        "tanggal_lahir": tanggal_lahir,
                        "jenis_kelamin": jenis_kelamin,
                        "lokasi": lokasi,
                        "lini_usaha": str(baris.get("lini_usaha", "")).strip(),
                        "cara_bayar": str(baris.get("cara_bayar", "")).strip(),
                        "jumlah_premi": str(baris.get("jumlah_premi", "")).strip(),
                        "uang_pertanggungan": str(baris.get("uang_pertanggungan", "")).strip(),
                        "cadangan_premi": str(baris.get("cadangan_premi", "")).strip(),
                        "capybmp": str(baris.get("capybmp", "")).strip(),
                        "jumlah_tertanggung": str(baris.get("jumlah_tertanggung", "")).strip(),
                        "flag_inspeksi": "PERLU INSPEKSI" if flag_tanggal else "OK",
                        "alasan_flag": alasan_flag if flag_tanggal else "",
                    })
                else:
                    hasil_tidak_valid.append({
                        "baris": i + 2,
                        "nama_pemegang": nama,
                        "nomor_identitas": nomor_identitas,
                        "alasan": " | ".join(kesalahan_alasan),
                        "bukti": " | ".join(kesalahan_bukti),
                    })

            progres.empty()

            st.session_state["hasil_valid"] = hasil_valid
            st.session_state["hasil_tidak_valid"] = hasil_tidak_valid
            st.session_state["total_baris"] = total

        if "hasil_valid" in st.session_state and "hasil_tidak_valid" in st.session_state:
            hasil_valid = st.session_state["hasil_valid"]
            hasil_tidak_valid = st.session_state["hasil_tidak_valid"]
            total = st.session_state["total_baris"]

            st.markdown("### Ringkasan Hasil Validasi")
            kolom_a, kolom_b, kolom_c = st.columns(3)
            kolom_a.metric("Total Baris", total)
            kolom_b.metric("Baris Valid", len(hasil_valid))
            kolom_c.metric("Baris Tidak Valid", len(hasil_tidak_valid))

            if hasil_tidak_valid:
                st.markdown("### Data Tidak Valid")
                st.caption(
                    "Tabel berikut menampilkan data yang tidak valid beserta alasan dan bukti kesalahannya. "
                    "Silakan perbaiki data pada berkas Excel, lalu unggah ulang."
                )
                df_tidak_valid = pd.DataFrame(hasil_tidak_valid)
                st.dataframe(df_tidak_valid, use_container_width=True)

                csv_tidak_valid = df_tidak_valid.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Unduh Data Tidak Valid (CSV)",
                    data=csv_tidak_valid,
                    file_name="data_tidak_valid.csv",
                    mime="text/csv",
                    key="bulk_unduh_tidak_valid",
                )
            else:
                st.success("Seluruh baris data valid.")

            if hasil_valid:
                st.markdown("### Data Valid")
                df_valid = pd.DataFrame(hasil_valid)

                jumlah_flag = len(df_valid[df_valid["flag_inspeksi"] == "PERLU INSPEKSI"])
                if jumlah_flag > 0:
                    st.warning(
                        f"Terdapat {jumlah_flag} baris data valid yang **perlu inspeksi** "
                        f"(tanggal polis tidak wajar)."
                    )

                st.dataframe(df_valid, use_container_width=True)

                df_flag = df_valid[df_valid["flag_inspeksi"] == "PERLU INSPEKSI"]
                if not df_flag.empty:
                    st.markdown("#### Data yang Perlu Inspeksi")
                    st.dataframe(
                        df_flag[["nomor_polis", "nama_pemegang", "tanggal_mulai",
                                 "tanggal_selesai", "alasan_flag"]],
                        use_container_width=True,
                    )

                    csv_flag = df_flag.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Unduh Data Perlu Inspeksi (CSV)",
                        data=csv_flag,
                        file_name="data_perlu_inspeksi.csv",
                        mime="text/csv",
                        key="bulk_unduh_flag",
                    )

                if st.button(
                    label="Simpan Data Valid ke Database",
                    use_container_width=True,
                    key="bulk_simpan_valid",
                ):
                    jumlah_disimpan = 0
                    jumlah_duplikat = 0
                    for record in hasil_valid:
                        record["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        disimpan = simpan_ke_database_valid(record)
                        if disimpan:
                            jumlah_disimpan += 1
                        else:
                            jumlah_duplikat += 1

                    if jumlah_disimpan > 0:
                        st.success(
                            f"{jumlah_disimpan} baris data valid berhasil disimpan ke database/data_valid.xlsx."
                        )
                    if jumlah_duplikat > 0:
                        st.warning(
                            f"{jumlah_duplikat} baris data dilewati karena sudah ada di database (duplikat)."
                        )
                    if jumlah_disimpan == 0 and jumlah_duplikat > 0:
                        st.info("Seluruh data sudah ada di database. Tidak ada data baru yang disimpan.")

                    del st.session_state["hasil_valid"]
                    del st.session_state["hasil_tidak_valid"]
                    del st.session_state["total_baris"]


# ============================================================
# TAB 2: DATABASE
# ============================================================
with tab_database:
    st.subheader("Database Data Polis Valid")
    st.caption(
        "Tab ini menampilkan seluruh data polis yang telah dinyatakan valid "
        "dan tersimpan dalam database."
    )

    path = "database/data_valid.xlsx"
    if os.path.exists(path):
        df_valid = pd.read_excel(path, dtype=str)
        st.metric("Total Data Valid", len(df_valid))
        st.dataframe(df_valid, use_container_width=True)

        st.download_button(
            label="Unduh Database (CSV)",
            data=df_valid.to_csv(index=False).encode("utf-8"),
            file_name="database_data_valid.csv",
            mime="text/csv",
            key="database_unduh_csv",
        )
    else:
        st.info("Belum terdapat data valid yang tersimpan pada database.")
