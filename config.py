from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 8000

class ProductionConfig(Config):
    DEBUG = False
    PORT = 5000