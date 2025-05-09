"""
API package initialization.
This module provides functions to create and configure the Flask-RESTx API.
"""

from flask import Flask
from flask_restx import Api

api = Api()

def create_api(app: Flask):
    """
    Initialize the API with the app and register all namespaces
    
    Args:
        app: Flask application instance
    
    Returns:
        Configured API instance
    """
    # Configure the API
    api.init_app(
        app,
        version=app.config.get('API_VERSION', '1.0'),
        title=app.config.get('API_TITLE', 'Production Optimization API'),
        description=app.config.get('API_DESCRIPTION', 'API for solving production optimization problems')
    )
    
    # Import namespaces here to avoid circular imports
    from api.endpoints.production import ns as production_ns
    
    # Register namespaces
    api.add_namespace(production_ns)
    
    return api