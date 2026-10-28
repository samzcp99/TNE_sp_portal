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
