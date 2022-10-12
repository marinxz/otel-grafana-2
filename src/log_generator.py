import logging
from logging import LogRecord
import logging_loki
import sys
"""
docker ps -qf "name=loki" | xargs -n 1 docker inspect | grep IPAddress
"""

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.trace_id = "123123123123123"
    return record


class TracingFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:
        record.tags = { "trace_id:": '1231231231', "span_id" : "aaaaa" }
        return True


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    # logging.setLogRecordFactory(record_factory)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    #   this changes severity to level for the log message level
    logging_loki.emitter.LokiEmitter.level_tag = "level"

    loki_handler = logging_loki.LokiHandler(
        url="http://172.18.0.4:3100/loki/api/v1/push",
        tags={"application": "test-app", "trace_id" : "00000", "span_id" : "zzzz" },
        version="1",
    )
    loki_handler.setLevel(logging.INFO)
    loki_handler.addFilter(TracingFilter())

    logger = logging.getLogger(__name__)
    logger.addHandler(loki_handler)

    for handler in root_logger.handlers:
        print(type(handler))
    for handler in logger.handlers:
        print(type(handler))

    for i in range(1, 2):
        logger.info("Test log " + str(i))


