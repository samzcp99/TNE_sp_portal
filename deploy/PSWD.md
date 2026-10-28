# PSWD deployment

- Upstream: https://github.com/remvze/pswd
- Source commit: 654fe86f87ce51ca063324aa6a77f8bae8a8e38d
- License: MIT; upstream LICENSE retained with source and deployment.
- Public URLs: https://sit.samzhao.cloud/tools/ and /tools/pswd/
- Server source: /opt/pswd/pswd-main
- Node build runtime: /opt/sit-build/node-v22.21.0-linux-x64/bin
- Static deployment: /var/www/sit.samzhao.cloud/current/tools/pswd
- No Docker or Node application service is required at runtime; Nginx serves static files.

Local changes: Astro subpath and site URL, prefixed static assets/fonts, Chinese portal navigation and reset guidance, cryptographic randomness for passphrase capitalization, explicit build-check dependency. Upstream generator UI and author attribution retained. Password generation occurs in the browser. localStorage stores generator preferences; generated passwords are held in React state and are not sent to a backend.

Rebuild on the server:

```sh
cd /opt/pswd/pswd-main
export PATH=/opt/sit-build/node-v22.21.0-linux-x64/bin:$PATH
export ASTRO_TELEMETRY_DISABLED=1
npm ci --ignore-scripts --no-audit --no-fund
npm run build
node verify-pswd.mjs
```

After checking the build, copy `dist/` into a new static release directory and switch the public `tools/pswd` symlink. Keep the previous directory for rollback. Deploy portal HTML after the tool itself is reachable. No DNS changes, additional ports, or additional certificates are needed.
