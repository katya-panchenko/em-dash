"""TellTale — a scenario-driven retail opportunity detector.

Pitch ≠ architecture: the engine is generic; all retailer/community/market
specifics live in scenario profiles under ``config/scenarios/``.
"""

__version__ = "0.1.0"

# Load .env (ANTHROPIC_API_KEY, Reddit creds) for any entry point. Optional dep.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass
