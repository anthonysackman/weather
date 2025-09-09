from sanic import Sanic
from sanic.response import html
from app.api.health import health_bp
from app.api.weather import weather_bp

app = Sanic("weather-api")

# Serve static files
app.static("/static", "./app/static")


# Basic frontend route
@app.get("/admin")
async def admin_page(request):
    with open("./app/templates/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return html(content)


# Register blueprints
app.blueprint(health_bp)
app.blueprint(weather_bp)

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
