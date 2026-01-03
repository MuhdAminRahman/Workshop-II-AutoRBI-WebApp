# Production Setup Guide

Complete guide to deploy AutoRBI to Render.

## Prerequisites

- GitHub repository connected
- Render account (free or paid)
- Cloudinary account
- Claude API key
- PostgreSQL connection string

## Step 1: Create PostgreSQL Database on Render

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. New → PostgreSQL
3. Fill in:
   - Name: `autorbi-db`
   - Database: `autorbi`
   - User: `autorbi_user`
   - Region: Your closest region
4. Click Create
5. Copy the "External Database URL"

## Step 2: Deploy Backend

### Create Web Service

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. New → Web Service
3. Connect GitHub repository
4. Fill in:
   - Name: `autorbi-api`
   - Environment: Python 3
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Region: Same as database

### Environment Variables

Click "Environment" and add:

DATABASE_URL=postgresql://...  (from PostgreSQL)
CLAUDE_API_KEY=sk-...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
SECRET_KEY=generate-random-string-here
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend-url.onrender.com

### Deploy

Click "Create Web Service" and wait for build to complete (5-10 minutes).

Test: Visit `https://autorbi-api.onrender.com/health`

## Step 3: Deploy Frontend

### Create Static Site

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. New → Static Site
3. Connect GitHub repository
4. Fill in:
   - Name: `autorbi-frontend`
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`
   - Region: Same as backend

### Environment Variables

Click "Environment" and add:

VITE_API_URL=https://autorbi-api.onrender.com
VITE_WS_URL=wss://autorbi-api.onrender.com

### Deploy

Click "Create Static Site" and wait for build (3-5 minutes).

Visit your frontend URL and test.

## Step 4: Database Migrations

### Run migrations on Render

Option A: Via Render Dashboard
1. Go to Web Service → Shell
2. Run: `cd backend && alembic upgrade head`

Option B: Locally (first time)
```bash
export DATABASE_URL=postgresql://...  # from Render
cd backend
alembic upgrade head
```

## Step 5: Seed Initial Data (Optional)
```bash
cd backend
python -m app.db.seed
```

## Troubleshooting

### Backend won't deploy
- Check build logs for errors
- Verify all environment variables are set
- Ensure `backend/requirements.txt` exists
- Check database connection string format

### Frontend shows blank page
- Check browser console for API connection errors
- Verify VITE_API_URL is correct
- Clear browser cache

### WebSocket connection fails
- Verify VITE_WS_URL uses `wss://` for HTTPS
- Check backend is running
- Review CORS settings

## Monitoring

### Check Backend Health
```bash
curl https://autorbi-api.onrender.com/health
```

### View Logs

1. Go to Web Service
2. Click "Logs"
3. Filter by level or search terms

### Database Backups

Render PostgreSQL provides automatic daily backups. Go to PostgreSQL instance → Backups.

## Scaling

For production with 50+ users:

1. **Backend**: Upgrade to paid plan (prevents auto-sleep)
2. **Database**: Monitor connections, upgrade if needed
3. **Storage**: Monitor Cloudinary usage
4. **API**: Monitor Claude API costs

## Security Checklist

- [ ] `SECRET_KEY` is strong random string (not visible in git)
- [ ] Database user has minimal required permissions
- [ ] HTTPS only (Render provides free SSL)
- [ ] CORS restricted to frontend domain
- [ ] No test data in production database
- [ ] Regular database backups enabled
- [ ] API keys rotated periodically
- [ ] Monitoring/alerting configured

## Rollback Procedure

If deployment breaks:

1. Go to Web Service → Deploy
2. Click previous successful deployment
3. Click "Redeploy"

Or redeploy from GitHub:
1. Make fix on main branch
2. Push to GitHub
3. Render auto-deploys

## Custom Domain (Optional)

1. Go to Web Service → Settings
2. Add Custom Domain
3. Update DNS records with CNAME provided by Render
4. Wait for SSL certificate (5-10 minutes)

---

See README.md for other documentation.