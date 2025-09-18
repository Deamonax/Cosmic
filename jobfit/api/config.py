import os

USE_LIVE_OPENAI = os.getenv("USE_LIVE_OPENAI", "false").lower() in {"1", "true", "yes"}
