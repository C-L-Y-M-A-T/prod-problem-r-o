"""
Main application entry point.
This module initializes and runs the Flask application.
"""

import os
from flask import Flask
from api import create_api
from config import config_by_name

def create_app(config_name='dev'):
    """
    Application factory function to create and configure the Flask app
    
    Args:
        config_name: Name of configuration to use (dev, test, prod)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object(config_by_name[config_name])
    
    # Initialize API
    create_api(app)
    
    return app

if __name__ == '__main__':
    # Get config name from environment or use 'dev' as default
    config_name = os.getenv('FLASK_CONFIG', 'dev')
    app = create_app(config_name)
    app.run(debug=app.config['DEBUG'])