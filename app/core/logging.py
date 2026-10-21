import logging

FORMAT='%(module)s: %(lineno)d %(levelname)-7s - %(message)s %(asctime)s.%(msecs)03d '

def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=FORMAT, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
