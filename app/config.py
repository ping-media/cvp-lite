import os

class Settings:
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE: str = "ypd_db"
    MONGODB_COLLECTION: str = "users"
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # Application Configuration
    APP_NAME: str = "CVP Lite"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

# Create settings instance
settings = Settings() 