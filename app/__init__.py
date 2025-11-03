from flask import Flask
from flask_bootstrap import Bootstrap
from config import DevelopmentConfig, ProductionConfig

app = Flask(__name__)
Bootstrap(app)
app.config.from_object(DevelopmentConfig)

from . import routes