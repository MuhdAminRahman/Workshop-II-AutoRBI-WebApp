# Development Guide

Detailed guide for local development and contribution.

## Development Setup

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env
nano .env

# Initialize database (first time)
alembic upgrade head

# Seed test data (optional)
python -m app.db.seed

# Run development server
uvicorn app.main:app --reload
```

**Backend runs at**: `http://localhost:8000`

**API Docs**: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Run development server
npm run dev
```

**Frontend runs at**: `http://localhost:5173`

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/auth-login` - New features
- `bugfix/extraction-crash` - Bug fixes
- `docs/update-readme` - Documentation

### 2. Make Changes

Edit code, test locally.

### 3. Commit with Conventional Commits
```bash
# Format: type(scope): description
git commit -m "feat(auth): add password reset functionality"
git commit -m "fix(extraction): handle large PDF files"
git commit -m "docs(readme): add deployment instructions"
git commit -m "test(analytics): add health score tests"
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`

### 4. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Go to GitHub and create Pull Request.

### 5. Review and Merge

Once approved, merge to `main` branch.

## Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_auth.py::test_login_success
```

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Generate coverage report
npm test -- --coverage
```

## Code Style

### Python
```bash
cd backend

# Format code (black)
black app/

# Check style (flake8)
flake8 app/

# Type checking (mypy)
mypy app/
```

### JavaScript/TypeScript
```bash
cd frontend

# Format code
npm run format

# Lint code
npm run lint

# Fix linting issues
npm run lint -- --fix
```

## Database Migrations

### Create New Migration
```bash
cd backend

# Alembic auto-generates based on model changes
alembic revision --autogenerate -m "add_new_field_to_user"

# Review generated migration in migrations/versions/
nano migrations/versions/xxx_add_new_field_to_user.py

# Apply migration
alembic upgrade head
```

### Rollback Migration
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade 001
```

## Common Development Tasks

### Add New API Endpoint

1. Create schema in `app/schemas/`
2. Create route in `app/api/`
3. Add service logic in `app/services/`
4. Test with Postman or cURL
5. Update API Contract documentation

### Add New React Component

1. Create component in appropriate `src/components/` folder
2. Create TypeScript types in `src/types/`
3. Add to `src/services/` if it needs API calls
4. Test in browser

### Add Environment Variable

1. Add to `.env.example` with documentation
2. Add to `app/config.py` (backend) or import in service (frontend)
3. Update documentation
4. Add to Render environment variables for production

## Debugging

### Backend Debugging
```python
# In FastAPI route
import logging

logger = logging.getLogger(__name__)

@app.get("/api/test")
def test_endpoint():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    return {"status": "ok"}
```

Access logs at: `http://localhost:8000/logs`

### Frontend Debugging
```typescript
// Browser console
console.log("Value:", value);
console.error("Error:", error);

// React DevTools browser extension
// Install from: https://react-devtools-tutorial.vercel.app/
```

### Database Debugging
```bash
# Connect to local PostgreSQL
psql postgresql://user:password@localhost:5432/autorbi

# List tables
\dt

# Query example
SELECT * FROM users;

# Exit
\q
```

## Performance Tips

### Backend
- Use database indexes on frequently queried columns
- Cache responses when appropriate
- Async operations for I/O (file upload, API calls)
- Connection pooling (configured in settings)

### Frontend
- Lazy load components with React.lazy()
- Use React.memo() for expensive components
- Optimize images
- Use TanStack Query for caching API responses

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
cd backend
pip install -r requirements.txt
```

### "npm ERR! Cannot find module 'react'"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### "CORS error" when calling backend from frontend

Check backend `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add frontend URL
)
```

### WebSocket connection fails

1. Check backend is running: `http://localhost:8000/health`
2. Check WebSocket URL in frontend `.env.local`
3. Verify token in WebSocket connection

## Git Workflow Summary
```bash
# Start new feature
git checkout -b feature/feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/feature-name

# Create PR on GitHub (web)
# After approval:

# Merge to main
git checkout main
git pull origin main
git merge feature/feature-name
git push origin main

# Delete feature branch
git branch -d feature/feature-name
git push origin --delete feature/feature-name
```

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Render Docs**: https://render.com/docs
- **Tailwind CSS**: https://tailwindcss.com/
- **TypeScript**: https://www.typescriptlang.org/

---

See README.md for overview and SETUP.md for production deployment.