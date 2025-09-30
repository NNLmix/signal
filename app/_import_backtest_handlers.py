
import logging
try:
    import app.telegram_backtest  # registers handlers on import
    logging.getLogger("tg_backtest").info("tg_backtest_import_ok")
except Exception as e:
    logging.getLogger("tg_backtest").error("tg_backtest_import_failed", extra={"error": str(e)})
