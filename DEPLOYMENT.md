# Deployment Guide

## Assumptions

- Ubuntu 24.04 droplet.
- `/srv/weather` holds the checked-out repo.
- `/etc/weather/.env` stores secrets.
- Bootstrap script has been run at least once (`scripts/bootstrap.sh`).

## Step 0: Update Secrets if Needed

1. `sudo vim /etc/weather/.env` (or `cat <<'EOF' > /etc/weather/.env ...` via CI).
2. Ensure permissions remain `600`.

## Step 1: Pull latest code and rebuild (manual)

```bash
sudo scripts/deploy.sh
```

This script now:

- Pulls the latest git commit from `main`.
- Ensures the SQLite file exists at `/etc/weather/weather_display.db`.
- Calls `docker compose` (via `compose.yaml`) to rebuild and restart the `weather-api` service.
- Uses `/etc/weather/.env` for configuration and the same path for the database.

### Local development overrides

If you want to run the Compose stack on your workstation, set the env vars so the service reads repo-local files:

```bash
export ENV_FILE=./etc/weather/.env
export DB_FILE=./weather_display.db
docker compose -f compose.yaml up -d --force-recreate --remove-orphans
```

The Compose file defaults to the `/etc/weather` paths but honors `ENV_FILE`/`DB_FILE` when they are provided, so you can keep secrets out of version control while still running locally.

## GitHub Actions automatic deploy

Once bootstrapped, pushes to `main` can automatically update the droplet.

### Secrets to store in GitHub

| Name | Description |
| --- | --- |
| `DO_HOST` | Droplet public IP or hostname |
| `DO_USER` | SSH user (`root` or sudo-enabled account) |
| `SSH_PRIVATE_KEY` | Private key that matches the droplet’s deploy key |
| `ASTRONOMY_API_ID` | Astronomy API app ID |
| `ASTRONOMY_API_SECRET` | Astronomy API secret |
| `DB_PATH` | Optional override for the SQLite file (default `/etc/weather/weather_display.db`) |
| `PORT` | Port the app should listen on (default `8000`) |

### Workflow behavior

On push to `main`:

1. Checkout the repo.
2. Load the SSH key, add GitHub + droplet host to `known_hosts`.
3. SSH into the droplet, rewrite `/etc/weather/.env` from GitHub Secrets, and secure the file.
4. Run `git pull` followed by `sudo scripts/deploy.sh`, which rebuilds the image and restarts the container.

You can find the workflow template in `.github/workflows/deploy.yml`. If you need to run environment-only updates (no code change), rerun the workflow or manually overwrite `/etc/weather/.env` and invoke `scripts/deploy.sh`.

## Step 2: Optional migrations

If a migration script is needed, run it inside the venv before `deploy.sh` or extend the script.

## Integrating with GitHub Actions

1. Add secrets: `DO_HOST`, `DO_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT` (if non-standard).
2. Workflow steps:
   - SSH into the droplet.
   - Copy updated `.env` (if changes exist).
   - Run `cd /srv/weather && sudo scripts/deploy.sh`.
3. Include `ssh-keyscan github.com >> /root/.ssh/known_hosts` to avoid prompts.
# Deployment Guide

## Automatic Migrations on Startup

The application now automatically runs database migrations on startup. This means:

✅ **Safe to deploy** - Migrations run automatically every time the server starts
✅ **Idempotent** - Safe to run multiple times, only applies missing changes
✅ **No shell access needed** - Perfect for platforms like Render free tier
✅ **Zero downtime** - Migrations run before the server accepts connections

## What Happens on Startup

1. **Migrations run** (`app/database/migrations.py`)
   - Checks current database schema
   - Applies only missing migrations
   - Logs what was applied
   
2. **Database initializes** (`app/database/db.py`)
   - Creates tables if they don't exist
   - Sets up indexes

3. **Server starts** - Ready to accept requests

## Migrations Applied Automatically

The system will automatically apply these migrations if needed:

1. **Multi-tenant users** - Adds `email`, `role`, `updated_at` to users
2. **API keys table** - Creates the `api_keys` table
3. **Device ownership** - Adds `user_id` to devices
4. **Secret tracking** - Adds `secret_viewed` to api_keys
5. **Pending secrets** - Adds `pending_secret` to api_keys

## Deployment Steps (Render)

### First Time Setup

1. **Create Web Service** on Render
   - Connect your GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app/main.py`

2. **Set Environment Variables**
   ```
   DEBUG=false
   PORT=8000
   DB_PATH=./weather_display.db
   ```

3. **Deploy** - Render will build and start automatically
   - Migrations run on first startup
   - Database is created automatically
   - Server starts and accepts connections

### Subsequent Deployments

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Render auto-deploys**
   - Pulls latest code
   - Installs dependencies
   - Starts server
   - **Migrations run automatically**
   - No manual intervention needed

## Creating Your First Admin User

After first deployment, create an admin user:

### Option 1: Using Render Shell (if available)
```bash
python create_admin.py admin your_password
```

### Option 2: Via API (if shell not available)
1. Register at `https://your-app.onrender.com/register`
2. Manually update database to make user admin:
   - Use Render's database browser (if available)
   - Or use a database client to connect
   - Run: `UPDATE users SET role = 'admin' WHERE username = 'your_username'`

### Option 3: Pre-seed in Code (temporary)
Add to `app/main.py` after `init_db()`:
```python
# Create default admin if none exists
from app.auth.utils import hash_password
from app.database.models import User
from datetime import datetime

users = await db.get_all_users()
if not users:
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("CHANGE_ME_IMMEDIATELY"),
        role="admin",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    await db.create_user(admin)
    logging.info("Created default admin user")
```

## Verifying Deployment

After deployment, check:

1. **Health endpoint**: `https://your-app.onrender.com/health`
   - Should return `{"status": "healthy"}`

2. **Docs page**: `https://your-app.onrender.com/docs`
   - Should load documentation

3. **Login page**: `https://your-app.onrender.com/login`
   - Should show login form

4. **Check logs** in Render dashboard:
   - Look for "Applied X migration(s)" or "Database schema is up to date"
   - Look for "Database initialized"
   - Look for "Starting worker"

## Troubleshooting

### Migrations not running?
Check logs for:
```
Checking for pending migrations...
✅ Applied X migration(s): ...
```

### Database locked errors?
- Render free tier uses ephemeral storage
- Database resets on each deploy
- Consider upgrading to persistent storage

### Can't create admin user?
- Use the registration endpoint first
- Then manually update role in database
- Or add temporary admin creation code

## Production Checklist

- [ ] Set `DEBUG=false` in environment variables
- [ ] Set strong passwords for admin users
- [ ] Use HTTPS (Render provides this automatically)
- [ ] Monitor logs for errors
- [ ] Test API key authentication
- [ ] Test device endpoints
- [ ] Verify user registration works
- [ ] Check admin panel access

## Rollback

If something goes wrong:

1. **Revert in GitHub**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Render auto-deploys** the previous version

3. **Migrations are idempotent** - Rolling back and forward is safe

## Database Persistence

⚠️ **Important for Render Free Tier:**
- Free tier uses ephemeral storage
- Database is lost on restart/redeploy
- For production, use:
  - Render Disk (paid)
  - External database (PostgreSQL, etc.)
  - Or accept that data resets on deploy

## Support

If you encounter issues:
1. Check Render logs
2. Verify environment variables
3. Test locally first
4. Check migration logs in startup output

