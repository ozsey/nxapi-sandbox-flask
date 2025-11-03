from app import app
from config import DevelopmentConfig, ProductionConfig

if __name__ == '__main__':
    app.config.from_object(DevelopmentConfig)
    app.run(port=DevelopmentConfig.PORT)