from flask import Flask
from flask.ext.cacheify import init_cacheify
import os

app = Flask(__name__)

cache = init_cacheify(app)
from slack import views
