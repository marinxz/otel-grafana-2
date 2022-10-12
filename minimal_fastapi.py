import logging
import sys
import logging_loki
from logging import LogRecord

from fastapi import FastAPI

from opentelemetry.instrumentation.logging import LoggingInstrumentor

from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

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


def setup_tracer( service_name ):
    """
    This one will try to set up tracer depending on the JAEGER_HOST
    if that one is not present not defined it presumes it is are operating
    in the cloud
    :param service_name:
    :return:
    """
    JAEGER_HOST="172.24.0.4"
    resource = Resource.create({SERVICE_NAME: service_name, 'app':'test-app' })
    tracer_provider = TracerProvider(resource=resource)
    #   Jaeger trace is running locally only
    # main_trace_exporter = JaegerExporter(
    #     # agent_host_name="127.0.0.1", "jaeger-host",
    #     agent_host_name=JAEGER_HOST,
    #     # agent_port=6831,
    #     agent_port=14268,
    # )

    tempo_ip = '172.26.0.2'
    main_trace_exporter = OTLPSpanExporter(
        endpoint="http://" + tempo_ip + ":4317"

    )

    tracer_provider.add_span_processor(
        # BatchSpanProcessor buffers spans and sends them in batches in a
        # background thread. The default parameters are sensible, but can be
        # tweaked to optimize your performance
        BatchSpanProcessor(main_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)

    return

setup_tracer("test-api")

#   this changes severity to level for the log message level
logging_loki.emitter.LokiEmitter.level_tag = "level"

loki_ip = '172.26.0.3'
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
formater = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d]' +
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
        logger.info('asda', extra= {'app_record_id': '12345678' })
        logger.info('First log in span no record')
        return {"message": "Hello World"}

