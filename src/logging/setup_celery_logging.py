import logging
import logging_loki
import sys

def setup_celery_logger( logger_to_set, app_name, loki_host ):
    """
    for now sets up loki logging
    :param root_logger:
    :param loki_host:
    :return:
    """
    logger_to_set.setLevel(logging.INFO)

    LOGGER_FORMAT_STRING = '%(levelname)s - %(asctime)s : %(message)s'
    loki_handler = logging_loki.LokiHandler(
        url="http://" + loki_host + ":3100/loki/api/v1/push",
        tags={'app': app_name},
        version="1",
    )
    loki_handler.setLevel(logging.INFO)
    loki_handler.setFormatter(logging.Formatter(LOGGER_FORMAT_STRING))
    logger_to_set.addHandler(loki_handler)

    stream_handler_found = False
    for handler in logger_to_set.handlers:
        if isinstance(handler, logging.NullHandler):
            continue
        if isinstance(handler, logging.StreamHandler):
            stream_handler_found = True

        handler.setFormatter(logging.Formatter(LOGGER_FORMAT_STRING))
        handler.setLevel(logging.INFO)

    if not stream_handler_found:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter(LOGGER_FORMAT_STRING))
        logger_to_set.addHandler(stream_handler)



def show_logger_structure(where, logger_obj):
    """
    useful for testing purposes
    """
    print("----------------------------------------------")
    print(where)
    print(f"logger id: {id(logger_obj)}")
    print(f"level: {logging.getLevelName(logger_obj.level)}")
    print(f"Parent: {logger_obj.parent}")
    print(f"Parent ID: {id(logger_obj.parent)}")
    print(f"Propagate: {logger_obj.propagate}")
    print(f"Handlers total: {len(logger_obj.handlers)}")
    for handler in logger_obj.handlers:
        print(type(handler), "level:", handler.level)

    if logger_obj.parent is None:
        return
    show_logger_structure("Parent structure ", logger_obj.parent)
