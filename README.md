# AnyCV API

AnyCV API is a FastAPI-based application built on a clean architecture design, providing robust API endpoints for the AnyCV application.

## Tech Stack

- **Framework**: FastAPI ([docs](https://fastapi.tiangolo.com/))
- **Database**: MongoDB with Mongoengine ODM ([docs](https://mongoengine.readthedocs.io/en/latest/index.html))
- **Authentication**: JWT tokens with refresh mechanism
- **Validation**: FastAPI's internal Pydantic v2 validation
- **File Storage**: Supabase Storage
- **Email Service**: Resend
- **External Services**: RapidAPI & Cloudflare Turnstile
- **Rate Limiting**: with slowapi
- **Logging**: with uvicorn
- **Deployment**: Render

## Key Features

- User authentication and authorization
- Profile management
- File uploads and management
- Email verification
- Cloudflare Turnstile integration for bot protection

## Architecture

The application follows Clean Architecture principles with three main layers:

1. **Core Layer** - Contains domain logic and interfaces

   - Domain: models & repository interfaces
   - Services & service interfaces
   - DTOs (Data Transfer Objects)
   - Exception handling

2. **Presentation Layer** - Handles API routing and request/response

   - Controllers (API routes)
   - Exception handlers

3. **Infrastructure Layer** - External integrations and data access
   - Persistence (MongoDB with Mongoengine)
   - External services like Cloudflare Turnstile and RapidAPI endpoints
   - Logging
   - File storage (Supabase)

## Getting Started - Local Development

### Prerequisites

Mandatory:

- Python 3.10+
- Install MongoDB Community Edition: [installation guide](https://www.mongodb.com/docs/manual/administration/install-community/)
- Get a supabase URL, either from [creating a hosted project in the cloud](https://supabase.com/) or [develop locally](https://supabase.com/docs/guides/local-development). (suggestion: use [self-hosting](https://supabase.com/docs/guides/self-hosting) with docker for local development)
- Create a [RapidAPI](https://rapidapi.com/) account & new application which uses the [LinkedIn Data API](https://rapidapi.com/mgujjargamingm/api/linkedin-data-scraper) to retrieve person data. Use the [/person](https://rapidapi.com/mgujjargamingm/api/linkedin-data-scraper/playground/apiendpoint_78e9b202-fd64-4c29-bc73-5cffbb11ee20) endpoint. Since this is the core of this application, it is necessary to create profiles.
- Create a [Cloudflare Account](https://www.cloudflare.com/) and a Turnstile Application to get a secret & site key. When creating a new turnstile application / site, put your localhost as domain (and other domains if you want to deploy this app, too), choose the **managed** option and select **no** on **pre-clearance**.

Optional:

- Create a [Resend](https://resend.com/home) account for email sending. If no RESEND_API_KEY is provided, sending emails will be skipped.

### Installation

1. Clone the repository

   ```bash
   git clone https://github.com/ZinoM21/any-cv-api
   cd any-cv-api
   ```

2. Create a virtual environment

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:

   ```
   # Server configuration
   PORT=8000                                   # The port your API will run on
   FRONTEND_URL=http://localhost:3000          # URL of your frontend for CORS settings
   MONGODB_URL=mongodb://localhost:27017       # MongoDB connection string (Note: dont put db_name here. Will be handled by mongoengine)

   # External Services
   RAPIDAPI_URL=https://linkedin-data-scraper.p.rapidapi.com/person # LinkedIn Data API endpoint URL. Don't change this!
   RAPIDAPI_HOST=linkedin-data-scraper.p.rapidapi.com # RapidAPI host for LinkedIn Data API. Don't change this!
   RAPIDAPI_KEY=<your-rapidapi-key>            # Your RapidAPI key for authentication
   TURNSTILE_SECRET_KEY=<your-turnstile-secret-key> # Cloudflare Turnstile secret for bot protection

   # Supabase Storage
   SUPABASE_URL=http://localhost:54321         # URL of your Supabase project (can also be a hosted one like https://yourproject.supabase.co)
   SUPABASE_PUBLISHABLE_KEY=<your-supabase-publishable-key> # Public key for Supabase client
   SUPABASE_SECRET_KEY=<your-supabase-secret-key> # Secret key for Supabase server-side operations

   # Email (leave these keys blank to not send emails)
   RESEND_API_KEY=<your-resend-api-key>        # API key for Resend email service
   RESEND_FROM_EMAIL=<your-from-email>         # Email address used as sender

   # Auth
   AUTH_SECRET=<your-auth-secret>              # Secret key for JWT token generation/validation. Note: shared with frontend!
   ```

5. Run the application

   ```bash
   uvicorn src.main:app --reload --log-level debug
   ```

6. Access the API documentation at `http://localhost:8000/docs`

7. Run an instance of the [AnyCV frontend](https://github.com/ZinoM21/any-cv-app)

## Development

### Project Structure

```
backend/
├── src/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── models/           # Domain models
│   │   │   └── interfaces/       # Repository interfaces
│   │   ├── services/             # Application services
│   │   ├── interfaces/           # Services & Other Infrastructure interfaces
│   │   ├── dtos/                 # Data Transfer Objects (i.e return types)
│   │   ├── exceptions/           # Domain exceptions
│   │   └── utils/                # Utility functions
│   ├── presentation/
│   │   ├── controllers/          # API routes
│   │   └── exceptions/           # HTTP exception handlers for presentation
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   └── configuration/    # Database setup
│   │   │   └── repositories/     # Repository implementations
│   │   ├── external/             # External service integrations
│   │   └── logging/              # Logging implementation
│   ├── config.py                 # Application configuration
│   ├── deps.py                   # Dependency injection with FastAPI
│   └── main.py                   # Application entry point
├── tests/                        # Unit and e2e tests
├── requirements.txt              # Python dependencies
└── render.yaml                   # Render deployment configuration
```

### Testing

Run tests with pytest:

```bash
pytest
```

Note: this will create a new `testdb` database in your mongoDB instance for e2e tests

### API Routes

The API provides the following main endpoints:

- **Auth**: `/v1/auth/*` - Authentication endpoints (register, login, refresh token)
- **User**: `/v1/users/*` - User management endpoints
- **Profile**: `/v1/profiles/*` - Profile management endpoints
- **File**: `/v1/files/*` - File upload and management endpoints

Full API documentation is available at the `/docs` endpoint when running the application. Or [view the hosted docs](https://api.buildanycv.com/docs)

## Deployment

The application is configured for deployment on Render using the `render.yaml` configuration file.

## License

MIT
