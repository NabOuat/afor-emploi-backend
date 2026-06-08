import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

class DevelopmentConfig(Config):
    """Configuration développement"""
    DEBUG = True
    TESTING = False
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Nabaga@localhost:5432/emploidb')

class ProductionConfig(Config):
    """Configuration production"""
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.getenv('DATABASE_URL')

class TestingConfig(Config):
    """Configuration test"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Nabaga@localhost:5432/emploidb_test')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
