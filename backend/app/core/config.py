import os

class Settings:
    PROJECT_NAME: str = "BIZINSIGHT"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bizinsight-production-grade-super-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database Configuration (PostgreSQL primary with seamless SQLite fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./bizinsight.db"
    )

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

settings = Settings()
