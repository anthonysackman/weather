from sanic import Sanic
from sanic.response import redirect
from app.api.health import health_bp
from app.api.datatest import main_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Sanic("weather-api")

# Serve static files
app.static("/static", "./app/static")


# Redirect old admin route to new main page
@app.get("/admin")
async def admin_redirect(request):
    return redirect("/")


# Register blueprints
app.blueprint(health_bp)
app.blueprint(main_bp)

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
