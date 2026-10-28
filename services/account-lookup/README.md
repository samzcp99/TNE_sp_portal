# Current status: OPEN (2026-10-28)

Re-enabled at the user's explicit request. Public URL: https://47.95.144.1/accounts_info.html. The service is enabled at boot, and the IP virtual host proxies the lookup API. Origin validation accepts the IP HTTPS origin. Existing exact-match and throttle protections remain. Current synthetic verification is verify_open.py; historical pause details below are superseded by this status.

# Current status: PAUSED (2026-10-28)

Public lookup is disabled while institutional authorization and data use arrangements are being clarified. Nginx returns 503; the systemd service is stopped and disabled. The public page has no form. Private data remains in restricted storage; no data deletion was performed. Do not re-enable merely by redeploying an older config. The technical instructions below describe the implementation before the pause.

# Student account lookup

Public form: https://sit.samzhao.cloud/accounts_info.html (also linked from /tools/).

Runtime: Python 3 standard library, systemd `sit-account-lookup`, loopback 127.0.0.1:8765. Nginx exposes only POST /api/account-lookup over existing HTTPS. No new public ports.

Current dataset: existing HUE HTML records (191). StudentInfo/HUE.xlsx has not been imported. Public HTML and JS contain no dataset. Private import file: StudentInfo/lookup-import.json (gitignored). Lookup requires exact school + Chinese student ID + Chinese surname. Compound surnames must be complete. Additional schools require explicit data import and school selection updates.

Private state: /var/lib/sit-account-lookup. `records.json` maps keyed HMAC lookup values to SIT IDs; `secret` is needed for imports and lookups. Both are root-owned and service-group-readable. SQLite stores timestamped keyed hashes for throttling; no names or request bodies are logged. Service runs without root privileges and is enabled at boot.

Limits: 20 attempts per IP per 10 minutes and 6 attempts per student ID per 15 minutes, persisted across service restarts. Nginx also limits requests per IP. Invalid/missing records share the same message. Results are no-store and disappear after 60 seconds or when the page is hidden. A student ID plus surname is a lightweight knowledge check, not strong authentication; this design cannot prove the requester's identity if both details are already known.

Updating records:

1. Prepare a private JSON array with school, student_id, surname, sit_id strings. Keep outside HUE and never publish it.
2. Transfer it to a root-only path on the same server.
3. Run `python3 /opt/sit-account-lookup/import_records.py /root/private-import.json`.
4. Restore root:sit-lookup ownership and 0640 mode on records.json and secret, then restart sit-account-lookup. Remove the temporary import file.
5. Preserve secret during backup/restore; changing it requires rebuilding every HMAC key from the private import data.

Verification: services/account-lookup/verify.py uses a temporary root-only fixture containing one real record. It checks successful exact lookup, mismatch privacy, input/origin validation, throttling, no embedded data and HTTPS headers; it never prints record values. Keep the fixture private and remove it after testing.
