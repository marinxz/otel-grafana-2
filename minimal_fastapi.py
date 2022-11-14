import logging
import sys
import logging_loki
from logging import LogRecord
import time

from fastapi import FastAPI, Request

from opentelemetry.instrumentation.logging import LoggingInstrumentor

from datetime import datetime

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

from src.telemetry.init_telemetry import init_telemetry_fastapi
from tasks import add, add_no_error

old_factory = logging.getLogRecordFactory()
def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.record_id = "00000"
    return record


class TracingFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:
        #record.record_id = record.__dict__['record_id']
        print(vars(record))
        if 'app_record_id' in record.args:
            record.app_record_id = record.args['app_record_id']
        else:
            record.app_record_id = ''
        return True


#   update this accordingly
loki_ip = '172.18.0.2'
tempo_host = '172.18.0.4'

init_telemetry_fastapi("fastapi-service", 'test-app', tempo_host)

#   this changes severity to level for the log message level
#   provjeri ovo
#   logging_loki.emitter.LokiEmitter.level_tag = "level"

loki_handler = logging_loki.LokiHandler(
    url="http://" + loki_ip + ":3100/loki/api/v1/push",
    tags={ 'app' : 'test-app'},
    version="1",
)
loki_handler.setLevel(logging.INFO)

app = FastAPI()
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stdout)
# logging.setLogRecordFactory(record_factory)
# logger.addHandler(stream_handler)
# formater = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d]' +
#             '[ trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s app_record_id=%(app_record_id)s ] - %(message)s')

formater = logging.Formatter('%(levelname)s [%(name)s] [%(filename)s:%(lineno)d]' +
            '[ trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s app_record_id=%(app_record_id)s ] - %(message)s')
loki_handler.setFormatter(formater)
loki_handler.addFilter(TracingFilter())
logger.addHandler(loki_handler)

for h in logger.handlers:
    print(h)
logger.setLevel(logging.INFO)

LoggingInstrumentor().instrument(set_logging_format=False)
FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

@app.get("/")
async def root():
    with tracer.start_as_current_span("message") as sp:
        logger.info('First log in span', {'app_record_id': '12345678' })
        logger.warning("One warning message")
        logger.info('asda', extra= {'app_record_id': '12345678' })
        logger.info('First log in span no record')
        return {"message": "Hello World"}

@app.get("/test")
async def test():
    """
    just test call to celery
    :return:
    """
    tracer = trace.get_tracer('__name__')
    print(tracer)
    with tracer.start_as_current_span("test-span"):
        logger.info('in test task tracer', {'app_record_id': '2222222' })
        now = datetime.now()
        print("Current Time =", now.strftime("%H:%M:%S"))
        with tracer.start_as_current_span("add-span"):
            res = add.delay(2,3,'test is parent')
            logger.info(f"result: {res}")
    return {"message": "Doing test: " + now.strftime("%H:%M:%S")}

@app.get("/test1")
async def test1():
    tracer = trace.get_tracer('__name__')
    with tracer.start_as_current_span("test-span") as sp:
        logger.info('in test test1 span')

        trace_id = sp.get_span_context().trace_id
        print("in test1:", trace_id)
        now = datetime.now()
        carrier = {}
        # Write the current context into the carrier.
        TraceContextTextMapPropagator().inject(carrier)
        print("New carrier:", carrier)
        res = add.delay(2,3,'test is parent', traceparent=carrier['traceparent'])
        print("result:", res)

    return {"message": "Doing test: " + now.strftime("%H:%M:%S")}

@app.get("/test2")
async def test2():
    tracer = trace.get_tracer('__name__')
    with tracer.start_as_current_span("test-span") as sp:
        logger.info('in test test1 span')

        trace_id = sp.get_span_context().trace_id
        print("in test2:", trace_id)
        now = datetime.now()
        carrier = {}
        # Write the current context into the carrier.
        TraceContextTextMapPropagator().inject(carrier)
        print("New carrier:", carrier)
        res = add_no_error.delay(2,3,'test is parent', traceparent=carrier['traceparent'])
        print("result:", res)

    return {"message": "Doing test 2: " + now.strftime("%H:%M:%S")}


@app.get("/test3")
async def test3(request: Request):
    tracer = trace.get_tracer('__name__')
    prop = TraceContextTextMapPropagator()
    time.sleep(1)
    logger.info('in test 3')
    if 'traceparent' in request.headers:
        print(request.headers['traceparent'])

        carrier = {'traceparent': request.headers['traceparent']}
        print(carrier)
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        print(ctx)
    else:
        ctx = None

    with tracer.start_as_current_span("test-span", context=ctx) as sp:
        trace_id = sp.get_span_context().trace_id
        logger.info("in test 3 span")
        print("in test2:", trace_id)
        now = datetime.now()
        carrier = {}
        # Write the current context into the carrier.
        TraceContextTextMapPropagator().inject(carrier)
        print("New carrier:", carrier)
        res = add_no_error.delay(2,3,'test is parent', traceparent=carrier['traceparent'])
        print("result:", res)

    return {"message": "Doing test with jaeger: " + now.strftime("%H:%M:%S")}
