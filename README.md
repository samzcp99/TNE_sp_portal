# Learning site

A mobile-oriented learning resource site and private server-side account lookup.

- `HUE/`: deployed static website, local Tabler assets and built PSWD tool.
- `services/account-lookup/`: private exact-match account lookup service.
- `services/feedback/`: support email templates and integration preparation.
- `tools/pswd-main/`: MIT-licensed upstream source plus local deployment changes.
- `deploy/`: Nginx/systemd settings and operational verification scripts.

Live site: https://sp.samzhao.cloud/ (direct IP HTTPS remains available).

Secrets, SSH keys, SMTP credentials, student records and runtime databases are excluded from Git. The repository contains no usable student dataset; account lookup requires a separately provisioned private dataset and key on the server. No Git remote is configured by default.

Source and configuration files are documentation of the deployment. Do not upload the whole repository into the web root: only `HUE/` is public. Private service state stays under `/var/lib/` and secrets under `/etc/`.
