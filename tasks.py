import logging

from celery import Celery
from celery.signals import celeryd_init, after_setup_task_logger, setup_logging, worker_process_init

# ---- used for tracing
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

from src.telemetry.init_telemetry import init_telemetry_celery
from src.logging.setup_celery_logging import setup_celery_logger, show_logger_structure

from time import sleep

logger = logging.getLogger(__name__)

BROKER_URL = 'redis://default:redis123@localhost:6379/1'
RESULT_URL = 'redis://default:redis123@localhost:6379/2'
app = Celery('tasks', broker=BROKER_URL, backend=RESULT_URL)

@celeryd_init.connect
def configure_workers(sender=None, conf=None, **kwargs):
    # this is cooked per https://github.com/celery/celery/issues/3599
    CELERY_WORKER_LOGGER_FORMAT_STRING = '%(levelname)s - %(asctime)s : %(message)s'
    CELERY_WORKER_TASK_LOGGER_FORMAT_STRING = '%(levelname)s - %(asctime)s Task %(task_name)s : %(message)s'

    # conf.worker_log_format  = CELERY_WORKER_LOGGER_FORMAT_STRING.format(sender)
    # conf.worker_task_log_format  = CELERY_WORKER_TASK_LOGGER_FORMAT_STRING.format(sender)
    # conf.worker_hijack_root_logger=False
    logger.info(f"in celeryd_init")


@setup_logging.connect
def config_loggers(*args, **kwags):
    loki_ip = '172.18.0.2'
    setup_celery_logger(logger, 'test-app-celery', loki_ip)
    logger.info(f"in setup_logging")
    print("in settup logging")
    show_logger_structure("Celery", logger)

@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    tempo_host = '172.18.0.4'
    init_telemetry_celery( 'Celery-service', 'test-app-celery', tempo_host)
    CeleryInstrumentor().instrument()

@app.task(name='add', bind=True)
def add(self, x, y, parent_str, **kwargs):
    print('in add kwargs:', kwargs)
    logger.info("In task add")
    tracer = trace.get_tracer(__name__)
    ctx = TraceContextTextMapPropagator().extract(carrier=kwargs)
    z = 0

    with tracer.start_as_current_span('do addition', context=ctx):
        z = x + y
        sleep(1)
        logger.info("In task add - calling task 2")

        task2.delay("param1", "param2")
        # raise ZeroDivisionError("Ups")
        current_span = trace.get_current_span()
        current_span.set_status(Status(StatusCode.ERROR))

    return z

@app.task(name='add_no_error', bind=True)
def add_no_error(self, x, y, parent_str, **kwargs):
    print('in add kwargs:', kwargs)
    logger.info("In task add no error")
    tracer = trace.get_tracer(__name__)
    ctx = TraceContextTextMapPropagator().extract(carrier=kwargs)
    z = 0

    with tracer.start_as_current_span('do addition', context=ctx):
        z = x + y
        sleep(1)
        task2.delay("param1", "param2")
        logger.info("In task add no error - calling task 2")
        # raise ZeroDivisionError("Ups")
        current_span = trace.get_current_span()
        current_span.set_status(Status(StatusCode.OK))

    return z


@app.task(name='task2', bind=True)
def task2(self, p1, p2):
    print("P1:", p1)
    print("P2:", p2)
    sleep(2)
    return