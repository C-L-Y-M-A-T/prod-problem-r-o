"""Configuration settings for the application"""

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    API_TITLE = 'Production Optimization API'
    API_VERSION = '1.0'
    API_DESCRIPTION = 'API for solving production optimization problems with Gurobi'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    # Production specific settings
    pass

# Configuration dictionary
config_by_name = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig
}