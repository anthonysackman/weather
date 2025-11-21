from sanic import Sanic
from sanic.response import redirect
from app.api.health import health_bp
from app.api.datatest import main_bp
from app.api.devices import devices_bp
from app.api.admin import admin_bp
from app.api.docs import docs_bp
from app.database.db import db
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("weather_api.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

app = Sanic("weather-api")

# Serve static files
app.static("/static", "./app/static")


# Initialize database on startup
@app.before_server_start
async def init_database(app, loop):
    """Initialize database before server starts."""
    # Reconfigure logging in worker process
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("weather_api.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override existing config
    )
    
    await db.init_db()
    logging.info("Database initialized")


# Register blueprints
app.blueprint(health_bp)
app.blueprint(main_bp)
app.blueprint(devices_bp)
app.blueprint(admin_bp)
app.blueprint(docs_bp)

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))
    # Default to debug mode for development (set DEBUG=false for production)
    debug_env = os.environ.get("DEBUG", "true").strip()
    debug = debug_env.lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, auto_reload=False, single_process=True)
