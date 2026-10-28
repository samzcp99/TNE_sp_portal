# Current status: LIVE DELIVERY

Enabled at the user's request on 2026-10-28. Public form uses /api/support/submit and a private durable outbox. To is server-configured; Cc is the student's validated email. No direct Helpdesk delivery. A systemd worker reads SMTP settings using LoadCredential; original credentials remain root-only and are not made readable by the web service.

Payloads are deleted after accepted, failed, partial or unknown outcomes; queued/retry payloads expire at 24 hours. Receipt metadata expires after 7 days. Worker cleanup runs at startup and every five minutes. Temporary known failures retry up to five times. Transmission uncertainty and interrupted sending are not automatically retried. Accepted means SMTP acceptance, not inbox placement.

New task limits: 50 per rolling day overall, 3 per student per 15 minutes, 5 per IP per 15 minutes. Duplicate submission IDs are session-bound and return the existing receipt. Status lookups require the same session and a random receipt token. Browser sessionStorage retains only the token and reference. The former preview endpoint remains available for isolated testing.

Automated tests never send email: test_contacts.py, test_preview.py and test_outbox.py. Historical preview notes below are superseded by this status.

# Student feedback mail delivery - preparation

Public website: https://sp.samzhao.cloud (IP access also retained).
From: Student Support <student@sp.samzhao.cloud>
To: support-recipient@example.invalid
Reply-To: the student's validated contact email
No automatic CC or delivery to Helpdesk; the recipient reviews and forwards manually.

Status: mail template and synthetic EML example prepared; no mail has been sent. No feedback submission endpoint is enabled yet. Do not claim successful delivery until SMTP accepts the message; report upstream rejection or timeout as failure/pending.

Recommended transport: Alibaba Cloud DirectMail SMTP. Required account-side setup: enable the service, select an appropriate region, verify the sending domain sp.samzhao.cloud using the exact DNS records supplied by DirectMail, create sender student@sp.samzhao.cloud, and set a dedicated SMTP password. Provider activation/billing and DNS records cannot be completed with the current SSH-only account access. Do not use the recipient's work account password.

Keep SMTP host, port, sender credentials and recipient allowlist in a server-only root-managed configuration file, never in public HTML/JS or source control. Use authenticated TLS SMTP. Public forms must not choose arbitrary recipients or sender addresses.

Email design: short English request by category; external student ID required; contact update/MFA includes new contact email, phone with country code, and reason. Free text remains student-supplied and must not be presented as staff-verified. No staff signature or school logo. Up to three validated/re-encoded images as attachments. No passwords, one-time codes or recovery codes.

Before enabling submission: implement fixed recipient delivery, schema/length checks, image decoding/re-encoding to remove metadata, size/pixel/attachment limits, persistent submission throttles, idempotency, explicit student notice/consent, restricted temporary storage and cleanup. Proposed retention: delete server-side files after successful sending; failed attempts expire within 24 hours. Mailbox copies follow the recipient institution's retention arrangements.

mailer.py only builds messages. Its attachment entry point expects images that have already been validated and re-encoded by the upload handler. Do not pass untrusted uploads directly into it.

## SMTP connection test (2026-10-28)

DirectMail region confirmed by user: cn-hangzhou. Authenticated TLS SMTP connection to smtpdm.aliyun.com:465 succeeded. Exactly one synthetic test message was accepted by the provider for the configured work recipient. User reports it arrived in Junk; inbox deliverability is not resolved. Public authoritative SPF, DKIM (selector aliyun-cn-hangzhou), DMARC and MX records exist. Need the receiving system's Authentication-Results and anti-spam report to identify the classification cause. No real student feedback has been sent and no public feedback submission endpoint has been enabled.

Credentials are held only in /etc/student-feedback/config.json (root-only) and the user's private local keys file (gitignored, restricted to the current Windows user). They are not in source code or public assets. Replace the disclosed password via private server configuration after rotation; never paste the replacement into chat.

## Public repository

This repository uses a placeholder recipient address. Production recipients are server-side configuration; set `SUPPORT_RECIPIENT` for standalone template generation, or read the private SMTP configuration and override the `To` header as demonstrated in test_delivery.py. Never commit real SMTP passwords, access keys, student records or screenshots. The SMTP test script is not a web endpoint and must only be run deliberately by the server administrator. The public support page remains preview-only and does not read the SMTP configuration or send mail.

## Student CC

Normal support messages include the validated student contact email in Cc and Reply-To. Use `delivery_addresses(message)` when sending so that Cc is included in the SMTP envelope; adding only a Cc header does not deliver the copy. The privacy notice explicitly covers the student receiving the same body and screenshots. The preview response shows the Cc address but still never sends mail. Synthetic transport tests explicitly set `cc_student=False` and send only to the configured work recipient, not example.com.

## Contact validation

Mainland China defaults to a separate +86 selector and requires an 11-digit mobile number matching 1[3-9] followed by nine digits. Pasted +86/86 prefixes and spacing are normalized; mail output always includes the country code. Other regions use local libphonenumber-js metadata in the browser and Python phonenumbers 9.0.42 on the server for offline format/length checks. The server-only Python dependency is installed under `/opt/student-feedback-preview/vendor`; install that version with `python3 -m pip install --target /opt/student-feedback-preview/vendor phonenumbers==9.0.42` when provisioning. Nothing is sent to a third-party phone validation API.

Private email must have valid syntax and a matching confirmation entry. Domain case and surrounding whitespace are normalized; local-part case is preserved. Syntax and numbering metadata checks do not establish ownership, delivery, or whether a phone is active. No OTP emails or SMS messages are sent by these checks.

Tests: `python3 test_contacts.py`, `python3 test_preview.py`, and `node test_contact_validation.js /path/to/HUE`.
