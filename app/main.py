import os
import warnings
import click

# ===============================
# Suppress GLib and Python warnings
# ===============================
os.environ["G_MESSAGES_DEBUG"] = ""
warnings.filterwarnings("ignore")

# ===============================
# Flask app imports
# ===============================
from . import create_app   # ✅ use relative import

# Create the Flask application
app = create_app()

# ===============================
# Run Flask locally (not needed on Gunicorn)
# ===============================
if __name__ == "__main__":   # ✅ correct main block
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
