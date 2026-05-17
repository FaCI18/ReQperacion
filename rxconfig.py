import reflex as rx

config = rx.Config(
    app_name="app",
    frontend_port=3000,
    backend_port=8000,
    api_url="http://localhost:8000",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
