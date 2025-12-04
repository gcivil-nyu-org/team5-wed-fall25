# AWS Elastic Beanstalk Deployment Guide - WebSocket Support

## Overview

This guide explains the changes needed to deploy the Django Channels WebSocket implementation to AWS Elastic Beanstalk.

## Key Changes Made

### 1. Procfile (NEW FILE)
**Location:** `/Procfile`

Tells Elastic Beanstalk to use Daphne (ASGI server) instead of Gunicorn (WSGI server):
```
web: daphne -b 0.0.0.0 -p 8000 CampusNest.asgi:application
```

### 2. Updated .ebextensions/django.config
**Changes:**
- ✅ Removed `WSGIPath` (no longer needed with Procfile)
- ✅ Added Nginx configuration for WebSocket support
- ✅ Configured WebSocket upgrade headers for `/ws/` routes
- ✅ Set proxy timeout to 86400 seconds (24 hours) for long-lived connections

## Deployment Steps

### Before Deploying

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "feat: Add Django Channels WebSocket support with Daphne"
   git push origin develop
   ```

2. **Verify requirements.txt includes:**
   - `channels==4.0.0`
   - `channels-redis==4.1.0`
   - `daphne==4.0.0`
   - `redis==5.0.0`

### Deploy to Elastic Beanstalk

**Option 1: Via Travis CI (Automatic)**
```bash
# Already set up - just push to develop branch
git push origin develop
```

**Option 2: Via EB CLI (Manual)**
```bash
eb deploy
```

**Option 3: Via AWS Console**
1. Navigate to Elastic Beanstalk console
2. Select your environment
3. Upload and Deploy → Upload new version
4. Upload your code as ZIP

### After Deployment - Testing

1. **Check WebSocket connection:**
   - Open browser DevTools (F12) → Network tab
   - Filter by "WS" (WebSocket)
   - Navigate to a message thread
   - You should see: `ws://your-app.elasticbeanstalk.com/ws/messages/thread/<id>/`
   - Status should be: **101 Switching Protocols** (success)

2. **Test real-time messaging:**
   - Open thread in two browsers with different users
   - Send a message from one browser
   - Message should appear instantly in the other browser (no refresh)

3. **Check logs:**
   ```bash
   eb logs
   # Look for:
   # - "Starting server at tcp:port=8000"
   # - "WSCONNECT /ws/messages/thread/X/"
   # - "User X connected to thread Y"
   ```

## Architecture on AWS

```
Internet → Load Balancer → Nginx (Port 8080) → Daphne (Port 8000) → Django Channels
                                    ↓
                            WebSocket Upgrade
                            (for /ws/* routes)
```

## Important Notes

### Using In-Memory Channel Layer (Current)
- ✅ Works for single-instance deployments
- ✅ No additional AWS costs
- ❌ Won't work with auto-scaling (multiple instances)
- ❌ WebSocket connections tied to specific instance

**Current configuration in settings.py:**
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

### Future: Redis Channel Layer (Phase 4)
For production scaling with multiple instances, you'll need Redis:

1. **Set up AWS ElastiCache (Redis):**
   - Create Redis cluster: `cache.t3.micro` (~$12/month)
   - Note the endpoint: `your-redis.cache.amazonaws.com:6379`

2. **Update settings.py:**
   ```python
   REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")

   if REDIS_ENDPOINT:
       CHANNEL_LAYERS = {
           "default": {
               "BACKEND": "channels_redis.core.RedisChannelLayer",
               "CONFIG": {
                   "hosts": [REDIS_ENDPOINT],
               },
           },
       }
   ```

3. **Add to .ebextensions/django.config:**
   ```yaml
   option_settings:
     aws:elasticbeanstalk:application:environment:
       REDIS_ENDPOINT: "your-redis.cache.amazonaws.com:6379"
   ```

## Troubleshooting

### WebSocket 404 Errors
**Symptom:** Browser shows "WebSocket connection failed: 404"

**Solution:** Nginx config not applied correctly
```bash
# SSH into EC2 instance
eb ssh

# Check if nginx config exists
cat /etc/nginx/conf.d/websocket.conf

# Restart nginx
sudo service nginx restart
```

### WebSocket 502 Bad Gateway
**Symptom:** WebSocket connects but immediately disconnects

**Solution:** Daphne not running or wrong port
```bash
# Check if Daphne is running
ps aux | grep daphne

# Check application logs
eb logs
```

### Messages Still Require Refresh
**Symptom:** WebSocket shows 101 but messages don't appear

**Possible causes:**
1. JavaScript cached - tell users to hard refresh (Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Verify WebSocket stays connected (doesn't disconnect after few seconds)

### WebSocket Disconnects After 60 Seconds
**Symptom:** Connection drops after 1 minute

**Solution:** Load balancer timeout too short
```bash
# Update load balancer idle timeout via AWS Console
# Elastic Beanstalk → Environment → Configuration → Load Balancer
# Set "Idle timeout" to 300 seconds (5 minutes) or higher
```

## Monitoring

### CloudWatch Metrics to Watch
- **ApplicationRequests5xx** - Should be low (<1%)
- **TargetResponseTime** - Should be <1s for HTTP, <100ms for WebSocket upgrade
- **HealthyHostCount** - Should equal instance count

### Custom Logging
Check Daphne logs for WebSocket activity:
```bash
eb logs | grep -E "WSCONNECT|WSDISCONNECT|User.*connected"
```

## Rollback Plan

If deployment fails:

1. **Via AWS Console:**
   - Environment → Application versions
   - Select previous version → Deploy

2. **Via EB CLI:**
   ```bash
   eb deploy --version <previous-version>
   ```

3. **Emergency fix:**
   ```bash
   # Revert Procfile to use Gunicorn
   echo "web: gunicorn CampusNest.wsgi:application" > Procfile
   git commit -am "Rollback to Gunicorn"
   git push origin develop
   ```

## Cost Estimation

**Current setup (single instance):**
- Elastic Beanstalk: Free tier or ~$5-15/month (t3.micro)
- No additional costs for WebSocket support

**With Redis (Phase 4):**
- ElastiCache (cache.t3.micro): ~$12/month
- Total: ~$17-27/month

## Security Considerations

✅ **Already configured:**
- Session-based authentication (Django sessions)
- Authorization checks (user must be thread participant)
- CSRF protection for initial page load

⚠️ **Consider adding:**
- Rate limiting for WebSocket messages (prevent spam)
- Message size limits (already: 2000 chars)
- Connection limits per user

## Success Criteria

After deployment, verify:
- ✅ Application loads normally (HTTP works)
- ✅ WebSocket connection succeeds (101 status)
- ✅ Messages send/receive in real-time (no refresh)
- ✅ Messages appear on correct side (sent vs received)
- ✅ Multiple users can chat simultaneously
- ✅ WebSocket reconnects after network interruption

## Need Help?

If you encounter issues:
1. Check logs: `eb logs`
2. SSH into instance: `eb ssh`
3. Test locally with Daphne first
4. Verify Nginx config is applied
5. Check CloudWatch metrics for 5xx errors
