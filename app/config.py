# app/config.py

import os
from dotenv import load_dotenv

def load_environment():
    env_file = ".env.prod" if os.getenv("RENDER") else ".env"
    load_dotenv(env_file)

class Config:
    def __init__(self):
        load_environment()
        self.env = os.getenv("ENV", "development")
        self.port = int(os.getenv("PORT", 5000))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

config = Config()

