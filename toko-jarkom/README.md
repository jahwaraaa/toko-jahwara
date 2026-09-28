# Toko Jahwara

Aplikasi pembelajaran Django dengan katalog dan pembelian di MongoDB, login/admin Django, dan deployment gratis.

## Jalankan lokal

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

MongoDB lokal memakai `mongodb://127.0.0.1:27018`. `.env.example` mencatat nama konfigurasi; untuk sesi PowerShell, set variabel yang diperlukan memakai `$env:NAMA_VARIABEL='nilai'`. Jangan commit file berisi connection string.

## Siapkan Atlas

1. Buat cluster Free di [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register), database user dengan hak `readWrite` pada database `toko`, lalu salin connection string `mongodb+srv://...`.
2. Masukkan URI sebagai environment variable `MONGODB_URI` dan nama database `MONGODB_DATABASE=toko`. Jangan tulis kredensial ke kode atau chat.
3. Sebelum memindahkan data lokal, set kedua URI di PowerShell lalu jalankan skrip. Skrip menyalin koleksi `supply` dan `purchases` tanpa menghapus data lokal.

```powershell
$env:LOCAL_MONGODB_URI = 'mongodb://127.0.0.1:27018'
$env:MONGODB_URI = '<connection-string-Atlas>'
$env:MONGODB_DATABASE = 'toko'
python migrate_mongodb_to_atlas.py
```

Untuk layanan Render Free, alamat keluar tidak tetap. Atlas mungkin perlu Network Access `0.0.0.0/0`; gunakan password database yang kuat dan batasi user hanya ke `readWrite` database aplikasi. Jangan simpan data sensitif. Free cluster memiliki batas 0,5 GB dan dapat dijeda setelah lama tidak aktif.

`seed.py` hanya menambahkan produk contoh yang belum ada; menjalankannya berulang tidak menghapus atau menimpa data produk.

## Deploy gratis

Blueprint [Render](https://render.com) ada di [../render.yaml](../render.yaml) pada root repository dan menunjuk ke folder aplikasi `toko-jarkom`; URL gratisnya berupa `https://toko-jahwara.onrender.com` (nama akhir mengikuti service Render).

1. Buat repository GitHub, lalu push kode. `.gitignore` mengecualikan virtualenv, `.env`, dan SQLite lokal.
2. Di Render, pilih **New → Blueprint**, hubungkan repository, lalu gunakan `render.yaml`.
3. Isi `MONGODB_URI` dengan URI Atlas. Untuk akun Django yang persisten, buat database PostgreSQL Free di [Neon](https://neon.tech) dan isi `DATABASE_URL` dari connection details Neon. Jika `DATABASE_URL` kosong, aplikasi memakai SQLite; pada Render Free file SQLite hilang saat service tidur/restart, termasuk akun dan sesi.
4. Sebelum deploy pertama, akun staf dapat dibuat terhadap Neon dari komputer lokal:

```powershell
$env:DATABASE_URL = '<connection-string-Neon>'
python manage.py migrate
python manage.py createsuperuser
```

Render Free menidurkan web service setelah 15 menit tanpa trafik; kunjungan pertama sesudahnya bisa memerlukan sekitar satu menit. Neon Free dan Atlas Free juga memiliki batas pemakaian. Paket ini untuk belajar/prototipe, bukan layanan produksi.

## Admin dan Google

- Dashboard staf: `/admin-panel/`; admin Django bawaan: `/admin/`. Buat akun staf memakai `createsuperuser`.
- Untuk Search Console, tambahkan URL publik sebagai **URL-prefix property**, pilih verifikasi HTML tag, isi nilai `content` tag tersebut sebagai environment variable `GOOGLE_SITE_VERIFICATION` di Render, deploy ulang, lalu klik **Verify**. Properti Domain memerlukan akses DNS.
- Render memberi subdomain gratis dan mendukung custom domain, tetapi nama domain milik sendiri biasanya perlu dibeli. Tambahkan domain itu pada setting service Render, atur DNS, lalu masukkan host ke `ALLOWED_HOSTS` dan origin `https://...` ke `CSRF_TRUSTED_ORIGINS`.
- Google Business Profile hanya untuk bisnis nyata yang melayani pelanggan di lokasi atau mendatangi pelanggan. Proyek belajar tanpa kegiatan usaha nyata tidak memenuhi syarat.