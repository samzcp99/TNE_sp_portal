# Current deployment: live support delivery

The form at https://sp.samzhao.cloud/support/ is enabled for real email delivery. It sends to the privately configured support recipient and copies the student's validated email. See services/feedback/README.md for the private outbox, limits and cleanup. Historical preview release notes below are superseded by this status.

# Learning site

A mobile-oriented learning resource site and private server-side account lookup.

- `HUE/`: deployed static website, local Tabler assets and built PSWD tool.
- `services/account-lookup/`: private exact-match account lookup service.
- `services/feedback/`: support email templates and integration preparation.
- `tools/pswd-main/`: MIT-licensed upstream source plus local deployment changes.
- `deploy/`: Nginx/systemd settings and operational verification scripts.

Live site: https://sp.samzhao.cloud/ (direct IP HTTPS remains available).

Secrets, SSH keys, SMTP credentials, student records and runtime databases are excluded from Git. The repository contains no usable student dataset; account lookup requires a separately provisioned private dataset and key on the server. GitHub repository: https://github.com/samzcp99/TNE_sp_portal.

Source and configuration files are documentation of the deployment. Do not upload the whole repository into the web root: only `HUE/` is public. Private service state stays under `/var/lib/` and secrets under `/etc/`.

## Support preview (v0.2)

- Preview URL: https://sp.samzhao.cloud/support/
- Self-hosted CAPTCHA: 5 characters, case-insensitive, session-bound, 120 seconds, single use; answers stored only as keyed hashes.
- Up to 3 screenshots, 3 MB each; JPEG/PNG/WebP decoded, limited to 8 MP, resized and re-encoded to strip metadata.
- `/api/support/preview` returns a short English email preview. It does not send email, create a ticket queue, read SMTP credentials, or persist feedback content/images.
- Independent `student-feedback-preview` systemd service on 127.0.0.1:8766, unprivileged user, Nginx proxy and request limits.
- SQLite stores CAPTCHA digests and rate-limit metadata in `/var/lib/student-feedback-preview`; no student dataset is used by this service.

Run synthetic service tests on the server:

```sh
cd /opt/student-feedback-preview
python3 test_preview.py
```

The preview is intended for review with fictional data. Production delivery and retry/receipt handling remain a separate future change. A self-hosted image CAPTCHA limits simple automation; it is not a strong identity check or protection against advanced OCR/bots.

Git tags: `v0.1-site-archive` preserves the pre-preview website; `v0.2-support-preview` preserves this preview. The local Git repository is connected to `origin` at https://github.com/samzcp99/TNE_sp_portal. Local ZIP snapshots are under `archives/` and exclude secrets and student records.
