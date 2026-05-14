# Upload Service

Microservice responsible for receiving architecture diagrams, storing them in S3, and publishing analysis jobs to SQS.

## Responsibilities
- `POST /api/v1/uploads` — Accept PNG/JPG/PDF files (max 20MB), store in S3, return `upload_id`
- `GET /api/v1/uploads/{upload_id}/status` — Return current processing status
- `PATCH /api/v1/uploads/{upload_id}/status` — Internal endpoint to update status (called by ai-processing-service)

## Architecture
Clean Architecture with 4 layers: Domain → Application → Infrastructure → API

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string |
| `AWS_REGION` | AWS region |
| `AWS_ENDPOINT_URL` | LocalStack endpoint (leave empty for real AWS) |
| `S3_BUCKET_NAME` | S3 bucket for storing diagrams |
| `SQS_QUEUE_URL` | SQS queue URL for analysis jobs |
| `INTERNAL_SERVICE_TOKEN` | Token for internal service-to-service calls |

## Running locally

```bash
cp .env.example .env
# Edit .env with your values

pip install -r requirements.txt
uvicorn src.api.main:app --port 8001 --reload
```

## Running tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Running with Docker

```bash
docker build -t upload-service .
docker run -p 8001:8001 --env-file .env upload-service
```

## API Endpoints

### POST /api/v1/uploads
```
Content-Type: multipart/form-data
X-API-Key: {api_key}

file: <binary>

Response 202:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "RECEIVED",
  "filename": "architecture.png",
  "created_at": "2026-05-08T10:30:00"
}
```

### GET /api/v1/uploads/{upload_id}/status
```
Response 200:
{
  "upload_id": "...",
  "status": "ANALYZED",
  "filename": "architecture.png",
  "created_at": "...",
  "updated_at": "...",
  "error_message": null
}
```
