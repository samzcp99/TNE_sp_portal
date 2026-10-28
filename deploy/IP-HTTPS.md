# IP HTTPS certificate

HTTPS on 47.95.144.1 uses a separate publicly trusted IP SAN certificate and redirects to https://sit.samzhao.cloud with the original path/query. Domain TLS is unchanged. HTTP IP access also redirects, except for the ACME validation path.

Client: /opt/certbot-ip/bin/certbot (5.4.0 in isolated Python venv)
Config: /etc/letsencrypt-ip
Certificate: /etc/letsencrypt-ip/live/server-ip/{fullchain,privkey}.pem
Challenge webroot: /var/lib/letsencrypt-ip
Timer: certbot-ip-renew.timer (every 4 hours, randomized up to 15 minutes)
Deploy hook: /etc/letsencrypt-ip/renewal-hooks/deploy/reload-nginx

Let's Encrypt IP certificates use the shortlived profile. Keep port 80 and the IP challenge location accessible for renewal. This certificate has separate renewal state from the original domain certificate and its existing certbot.timer.

Verified: public IP TLS without bypassing certificate verification; redirect ends at domain HTTPS 200; domain/toolbox HTTPS 200; IP renewal dry run and Nginx deploy hook succeed.

Official guide: https://letsencrypt.org/2026/03/11/shorter-certs-certbot/
