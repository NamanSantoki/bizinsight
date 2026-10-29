import os

class Settings:
    PROJECT_NAME: str = "BIZINSIGHT"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bizinsight-production-grade-super-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database Configuration (PostgreSQL primary with seamless SQLite fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./bizinsight.db"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # CORS — comma-separated origins in env, or defaults for dev
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://localhost:8080,http://localhost"
    ).split(",")

    # Storage paths
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/raw")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "./data/processed")
    SAMPLES_DIR: str = os.getenv("SAMPLES_DIR", "./data/samples")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "./ml/models")

    # Ollama / Local LLM configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Query execution safety
    MAX_QUERY_TIMEOUT_SECONDS: int = 15
    MAX_QUERY_ROW_LIMIT: int = 1000

    # Enterprise connectors
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    API_KEY_DEFAULT_EXPIRY_DAYS: int = int(os.getenv("API_KEY_DEFAULT_EXPIRY_DAYS", "90"))

settings = Settings()
