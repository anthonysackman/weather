# Production Migration Guide

## 🚨 Pre-Migration Checklist

- [ ] Schedule maintenance window (5-10 minutes)
- [ ] Notify users of downtime
- [ ] Have rollback plan ready
- [ ] Test migration on staging/dev first
- [ ] Backup current database
- [ ] Verify backup is valid

## 📋 Migration Steps

### Step 1: Prepare

```bash
# SSH into production server
ssh user@your-production-server

# Navigate to app directory
cd /path/to/weather-api

# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Verify you have the migration script
ls -la migrate_production.py
```

### Step 2: Stop the Service

**For systemd:**
```bash
sudo systemctl stop weather-api
sudo systemctl status weather-api  # Verify it's stopped
```

**For Docker:**
```bash
docker stop weather-api
docker ps  # Verify it's stopped
```

**For PM2:**
```bash
pm2 stop weather-api
pm2 status  # Verify it's stopped
```

### Step 3: Run Migration

```bash
# Run the production-safe migration script
python migrate_production.py
```

The script will:
1. ✅ Verify database state
2. ✅ Create timestamped backup
3. ✅ Ask for confirmation
4. ✅ Run migration in transaction
5. ✅ Auto-rollback on failure
6. ✅ Verify results

**Expected Output:**
```
============================================================
🚀 Weather API - Production Database Migration
============================================================

1️⃣  Pre-flight Checks

📊 Current Database State:
   Users: 3
   Devices: 5
   User columns: id, username, password_hash, created_at

⚠️  WARNING: This will modify your database!
   A backup will be created automatically.

Proceed with migration? (yes/no): yes

2️⃣  Creating Backup
✅ Backup created: ./weather_display.db.backup.20241121_153045

3️⃣  Running Migration
🔄 Running migration...
   📝 Reading existing data...
   🗑️  Dropping old tables...
   📊 Creating new schema...
   📇 Creating indexes...
   👥 Migrating users...
      ✓ admin (role: admin)
      ✓ user1 (role: user)
      ✓ user2 (role: user)
   📱 Migrating devices...
      ✓ 5 devices migrated

✅ Migration completed successfully!

📊 Post-Migration State:
   Users: 3
   Devices: 5

============================================================
✅ MIGRATION SUCCESSFUL!
============================================================

📁 Backup saved at: ./weather_display.db.backup.20241121_153045

📋 Next Steps:
   1. Test your application
   2. Generate API keys for users in admin panel
   3. Update ESP32 devices with new authentication

💡 To rollback: mv ./weather_display.db.backup.20241121_153045 ./weather_display.db
```

### Step 4: Start the Service

**For systemd:**
```bash
sudo systemctl start weather-api
sudo systemctl status weather-api  # Verify it's running
```

**For Docker:**
```bash
docker start weather-api
docker logs -f weather-api  # Watch logs
```

**For PM2:**
```bash
pm2 start weather-api
pm2 logs weather-api  # Watch logs
```

### Step 5: Verify

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test admin login
curl -X GET http://localhost:8000/api/devices \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)"

# Check database
sqlite3 weather_display.db "SELECT username, role FROM users;"
```

**Expected:**
```
admin|admin
user1|user
user2|user
```

## 🔄 Rollback Procedure

If something goes wrong:

### Option 1: Automatic (if migration failed)
The script automatically rolls back on failure.

### Option 2: Manual Rollback

```bash
# Stop service
sudo systemctl stop weather-api  # or docker stop / pm2 stop

# Restore backup (use the backup path from migration output)
mv weather_display.db.backup.20241121_153045 weather_display.db

# Start service
sudo systemctl start weather-api  # or docker start / pm2 start

# Verify
curl http://localhost:8000/health
```

## 🐳 Docker-Specific Instructions

### If using Docker Compose:

```bash
# Stop services
docker-compose down

# Backup volume
docker run --rm \
  -v weather_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/weather_backup_$(date +%Y%m%d).tar.gz /data

# Run migration
docker-compose run --rm api python migrate_production.py

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### If using standalone Docker:

```bash
# Stop container
docker stop weather-api

# Backup database file
docker cp weather-api:/app/weather_display.db ./weather_display.db.backup

# Run migration in container
docker run --rm \
  -v weather-data:/app/data \
  -v $(pwd)/migrate_production.py:/app/migrate_production.py \
  weather-api:latest \
  python migrate_production.py

# Start container
docker start weather-api
```

## 🧪 Testing After Migration

### 1. Test Admin Access
```bash
curl -X GET http://localhost:8000/api/devices \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)"
```

### 2. Test Device Endpoints
```bash
# Should still work with device_id only (backward compatible)
curl http://localhost:8000/api/device/YOUR_DEVICE_ID/esp
```

### 3. Verify Database
```bash
sqlite3 weather_display.db << EOF
.tables
.schema users
.schema devices
.schema api_keys
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as device_count FROM devices;
EOF
```

## 📊 Post-Migration Tasks

### 1. Update User Emails
Users will have placeholder emails (`username@example.com`). Update them:

```bash
# Via SQLite
sqlite3 weather_display.db
UPDATE users SET email = 'real@email.com' WHERE username = 'admin';
```

Or via admin panel (once implemented).

### 2. Generate API Keys
API keys will be generated through the admin panel (Phase 3).

### 3. Update ESP32 Devices
Once HMAC authentication is implemented (Phase 2), you'll need to:
1. Generate API key for each user
2. Flash ESP32 with device_id + api_key
3. Update ESP32 code to sign requests

## 🚨 Troubleshooting

### Migration fails with "table already exists"
```bash
# Database might be partially migrated
# Restore from backup and try again
mv weather_display.db.backup.TIMESTAMP weather_display.db
python migrate_production.py
```

### Service won't start after migration
```bash
# Check logs
sudo journalctl -u weather-api -f  # systemd
docker logs weather-api  # docker
pm2 logs weather-api  # pm2

# Common issue: Missing dependencies
pip install -r requirements.txt
```

### Devices not showing up
```bash
# Check device ownership
sqlite3 weather_display.db "SELECT device_id, user_id, name FROM devices;"

# All devices should be assigned to user_id 1 (first admin)
```

## 📞 Support

If you encounter issues:
1. Check the backup was created: `ls -la weather_display.db.backup.*`
2. Rollback if needed
3. Check application logs
4. Verify database schema: `sqlite3 weather_display.db ".schema"`

## ✅ Success Criteria

Migration is successful when:
- [x] Service starts without errors
- [x] Admin can login
- [x] Devices are visible in admin panel
- [x] Device endpoints return weather data
- [x] All users have `role` field
- [x] All devices have `user_id` field
- [x] `api_keys` table exists

## 🎯 Next Phase

After successful migration:
- **Phase 2**: Implement HMAC authentication
- **Phase 3**: Update admin panel with user/key management
- **Phase 4**: Create user dashboard
- **Phase 5**: Add registration page

