# Next Steps

1. **Lock down the current stack**
   - Keep the Sanic app, flexible auth, API key UX, and automatic migrations exactly as they are today.
   - Verify the docs/README already capture the production readiness work.
   - Preserve the SQLite file on the VPS (and keep the migration script running on every start).

2. **Provision the self-hosted server**
   - Spin up the cheap VPS of your choice (DigitalOcean, Hetzner, Linode, etc.).
   - Install Docker (or just Python/virtualenv if you prefer) and open the necessary ports.
   - Mount persistent storage for `/app/data/weather_display.db` and configure backups (cron copy or rsync).

3. **Build a deploy pipeline**
   - Push the repo to GitHub (already in place).
   - Add a CI workflow that builds the Docker image (or tarball), tests the repo, and publishes artifacts (Docker Hub or directly to the VPS).
   - On the VPS, provide a deploy script that pulls the latest artifact, replaces the running container, and lets the automatic migrations run at startup.

4. **Harden and monitor**
   - Continue to avoid personal identifiers (use usernames, not emails, in the UI/logs).
   - Enable HTTPS via a reverse proxy (Caddy/nginx) and configure firewall rules.
   - Rotate API keys periodically and monitor logs for unauthorized attempts.

5. **Future expansion**
   - When you’re ready, add a second data store (Postgres/Timescale) for aggregated device data and keep SQLite for config/auth.
   - Build an ingestion endpoint or worker to funnel late-night device reports into that time-series table.
   - Extend the dashboard/admin UI with analytics once the aggregation store is in place.

