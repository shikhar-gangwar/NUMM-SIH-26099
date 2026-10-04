import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "National Unified Material Master Framework"
    ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/sih_master"
    JWT_SECRET: str = "change-this-in-production-to-a-secure-secret-key-32-chars"
    JWT_ACCESS_TTL_MIN: int = 30
    SEED_ADMIN_PASSWORD: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Provider Settings (sentence_transformers, qwen3_0_6b, tfidf, fake)
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    EMBEDDING_BATCH_SIZE: int = 64
    EMBEDDING_DEVICE: str = "cpu"
    
    # Qwen v2.x Settings
    QWEN_EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"
    QWEN_EMBEDDING_DIM: int = 1024
    QWEN_RERANKER_MODEL: str = "Qwen/Qwen3-Reranker-0.6B"
    
    RERANKER_PROVIDER: str = "none"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_TOP_N: int = 20
    
    LLM_PROVIDER: str = "none"
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    
    # Path settings
    MATCH_CONFIG_PATH: str = "config/scoring.yaml"
    CATEGORY_PACKS_DIR: str = "config/category_packs"
    ABBREVIATIONS_PATH: str = "config/abbreviations.yaml"
    STANDARD_EQUIV_PATH: str = "config/standard_equivalence.yaml"
    SIZE_TABLES_PATH: str = "config/size_tables.yaml"
    UOM_PATH: str = "config/uom.yaml"
    MATERIAL_ALIASES_PATH: str = "config/material_aliases.yaml"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
