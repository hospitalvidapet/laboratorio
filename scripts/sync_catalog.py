from app import create_app
from app.catalog_sync import synchronize_catalog

app = create_app()
with app.app_context():
    result = synchronize_catalog(trigger="command")
    print(result)
    raise SystemExit(0 if result.get("ok") else 1)
