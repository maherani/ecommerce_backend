import logging


class RequestLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)

        request_method = getattr(record, "request_method", None)
        request_path = getattr(record, "request_path", None)
        status_code = getattr(record, "status_code", None)
        duration_ms = getattr(record, "duration_ms", None)
        request_id = getattr(record, "request_id", None)

        if request_method and request_path:
            message = (
                f"{message} "
                f"method={request_method} "
                f"path={request_path}"
            )

        if status_code is not None:
            message = f"{message} status={status_code}"

        if duration_ms is not None:
            message = f"{message} duration_ms={duration_ms:.2f}"
            
        if request_id:
            message = f"{message} request_id={request_id}"
            
        return message


def configure_logging() -> None:
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        RequestLogFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
