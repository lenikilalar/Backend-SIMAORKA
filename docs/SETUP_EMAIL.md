# Email Service Setup Guide

Panduan lengkap untuk mengkonfigurasi layanan email di SIMAORKA Backend.

---

## Quick Setup (Development)

Untuk development, email akan ditampilkan di console:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Email tidak benar-benar dikirim, hanya ditampilkan di terminal server.

---

## Gmail SMTP Setup

### 1. Aktifkan 2-Step Verification

1. Buka [Google Account Security](https://myaccount.google.com/security)
2. Aktifkan **2-Step Verification**

### 2. Generate App Password

1. Buka [App Passwords](https://myaccount.google.com/apppasswords)
2. Pilih **Mail** dan **Other (Custom name)**
3. Masukkan nama: `SIMAORKA`
4. Copy password 16-karakter yang dihasilkan

### 3. Konfigurasi .env

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=SIMAORKA <youremail@gmail.com>
```

> ⚠️ **Penting**: Gunakan App Password, bukan password Gmail biasa!

---

## Alternatif: Mailtrap (Testing)

[Mailtrap](https://mailtrap.io) menangkap email tanpa mengirim ke inbox asli.

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=sandbox.smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_mailtrap_username
EMAIL_HOST_PASSWORD=your_mailtrap_password
DEFAULT_FROM_EMAIL=SIMAORKA <noreply@simaorka.id>
```

---

## Alternatif: SendGrid

[SendGrid](https://sendgrid.com) - 100 email/hari gratis.

### 1. Buat API Key

1. Daftar di SendGrid
2. Buat API Key dengan permission **Mail Send**

### 2. Konfigurasi

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxx.xxxxx
DEFAULT_FROM_EMAIL=SIMAORKA <noreply@yourdomain.com>
```

---

## Alternatif: Mailgun

[Mailgun](https://mailgun.com) - 5000 email/bulan gratis (3 bulan).

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
DEFAULT_FROM_EMAIL=SIMAORKA <noreply@your-domain.mailgun.org>
```

---

## Alternatif: Amazon SES

[Amazon SES](https://aws.amazon.com/ses/) - Pay per use ($0.10/1000 emails).

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-user
EMAIL_HOST_PASSWORD=your-ses-smtp-password
DEFAULT_FROM_EMAIL=SIMAORKA <noreply@yourdomain.com>
```

---

## Testing Email Configuration

### Via Django Shell

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    subject='Test Email SIMAORKA',
    message='Ini adalah test email.',
    from_email='noreply@simaorka.id',
    recipient_list=['your-email@example.com'],
    fail_silently=False,
)
```

### Via API (Password Reset)

```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## Troubleshooting

### "Authentication failed"

- Gmail: Pastikan menggunakan **App Password**, bukan password biasa
- Periksa 2-Step Verification sudah aktif
- Cek EMAIL_HOST_USER dan EMAIL_HOST_PASSWORD

### "Connection refused"

- Periksa EMAIL_PORT (587 untuk TLS, 465 untuk SSL)
- Firewall mungkin memblokir port SMTP
- Coba ganti EMAIL_USE_TLS ke EMAIL_USE_SSL untuk port 465

### "Sender address rejected"

- Pastikan DEFAULT_FROM_EMAIL menggunakan email yang terverifikasi
- Untuk SendGrid/Mailgun, verifikasi domain dulu

### Email masuk ke Spam

- Setup SPF, DKIM, dan DMARC record di DNS
- Gunakan domain sendiri, bukan gmail.com
- Hindari kata-kata spam di subject/body

---

## Production Checklist

- [ ] Gunakan SMTP provider profesional (SendGrid/Mailgun/SES)
- [ ] Setup domain sendiri untuk FROM email
- [ ] Konfigurasi SPF record di DNS
- [ ] Konfigurasi DKIM signing
- [ ] Test email masuk inbox (bukan spam)
- [ ] Monitor bounce rate dan complaints

---

## Environment Variables Summary

| Variable | Development | Production |
|----------|-------------|------------|
| EMAIL_BACKEND | `...console.EmailBackend` | `...smtp.EmailBackend` |
| EMAIL_HOST | - | smtp.gmail.com |
| EMAIL_PORT | - | 587 |
| EMAIL_USE_TLS | - | True |
| EMAIL_HOST_USER | - | your-email |
| EMAIL_HOST_PASSWORD | - | app-password |
| DEFAULT_FROM_EMAIL | - | SIMAORKA \<email\> |
| FRONTEND_URL | http://localhost:3000 | https://simaorka.id |
