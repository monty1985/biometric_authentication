# Voice-Based Authentication API

A secure, scalable, and modular voice authentication system for enterprise applications.

## Features

- Voice embedding generation using ECAPA-TDNN
- Anti-spoofing protection against replay attacks and deepfakes
- Secure vector storage for voice embeddings
- RESTful API for enrollment and verification
- Multi-tenant support with API key management
- Comprehensive audit logging

## System Architecture

```
[Client App (Web)]
   ⇄  API Gateway
         ⇄ Auth Controller
             ⇄ Voice Embedding Module (ECAPA-TDNN)
             ⇄ Anti-Spoofing Module (SpeechBrain ASVspoof)
             ⇄ ASR Prompt Validator
             ⇄ Embedding Store (Vector DB)
             ⇄ Authentication Engine
             ⇄ Audit Logger
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/enroll` - Enroll a new user with voice sample
- `POST /api/v1/auth/verify` - Verify a user's voice
- `POST /api/v1/auth/check-liveness` - Check for voice liveness

### Management

- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/metrics` - System metrics (requires authentication)

## Security Features

- Voice embedding using ECAPA-TDNN
- Anti-spoofing using SpeechBrain ASVspoof
- Secure vector storage with FAISS
- API key authentication
- Comprehensive audit logging
- Rate limiting and request validation

## Development

### Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── router.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── models/
│   │   │   └── voice.py
│   │   │
│   │   ├── services/
│   │   │   ├── embedding.py
│   │   │   ├── anti_spoof.py
│   │   │   └── auth.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │
│   ├── .env.example
│   │
│   └── requirements.txt
│
└── README.md
```

## License

MIT License 