# SnapSort Backend

## Project Structure

snapsort-backend/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config/
│   │   ├── settings.py            # Environment configuration
│   │   └── database.py            # Database connection
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── group.py
│   │   └── photo.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── organization.py
│   │   ├── group.py
│   │   └── photo.py
│   │
│   ├── routers/                   # API routes
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── organizations.py
│   │   ├── groups.py
│   │   └── photos.py
│   │
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   ├── group_service.py
│   │   ├── photo_service.py
│   │   └── face_service.py
│   │
│   ├── ai/                        # AI/ML components
│   │   └── providers/
│   │       ├── base.py            # Abstract provider interface
│   │       ├── deepface_provider.py
│   │       ├── insightface_provider.py
│   │       ├── aws_provider.py
│   │       └── google_provider.py
│   │
│   ├── storage/                   # Cloud storage (TODO)
│   ├── workers/                   # Background tasks (TODO)
│   └── utils/
│       └── security.py            # JWT & auth utilities
│
├── alembic/                       # Database migrations
├── tests/                         # Unit & integration tests
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Docker services
├── Dockerfile                     # Application container
└── README.md                      # This file


## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Start Services (Docker)

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Qdrant (port 6333)

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Run Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc


## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| Vector DB | Qdrant |
| Storage | AWS S3 + Cloudinary |
| Task Queue | Celery + Redis |
| Face Recognition | DeepFace, InsightFace, AWS Rekognition, Google Vision |


## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh tokens
- `POST /auth/register-face` - Upload face for recognition

### Groups
- `POST /groups` - Create group
- `GET /groups` - List user's groups
- `POST /groups/{id}/members` - Add member
- `DELETE /groups/{id}/members/{user_id}` - Remove member

### Photos
- `POST /photos/groups/{id}/upload` - Upload photos
- `GET /photos/groups/{id}` - Get YOUR photos in group
- `GET /photos/{id}/download` - Download photo
- `POST /photos/bulk-download` - Download multiple as ZIP


## License

Private - All rights reserved
