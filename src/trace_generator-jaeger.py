import sys
import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from datetime import datetime

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
"""
docker ps -qf "name=tempo" | xargs -n 1 docker inspect | grep IPAddress
"""

class RecordsListHandler(logging.Handler):
    """
    A handler class which stores LogRecord entries in a list
    """
    def __init__(self, records_list):
        """
        Initiate the handler
        :param records_list: a list to store the LogRecords entries
        """
        self.records_list = records_list
        super().__init__()

    def emit(self, record):
        self.records_list.append(record)

def setup_tracer( service_name ):
    """
    This one will try to set up tracer depending on the JAEGER_HOST
    if that one is not present not defined it presumes it is are operating
    in the cloud
    :param service_name:
    :return:
    """
    JAEGER_HOST="172.18.0.3"
    resource = Resource.create({SERVICE_NAME: service_name })
    tracer_provider = TracerProvider(resource=resource)
    #   Jaeger trace is running locally only
    # main_trace_exporter = JaegerExporter(
    #     # agent_host_name="127.0.0.1", "jaeger-host",
    #     agent_host_name=JAEGER_HOST,
    #     # agent_port=6831,
    #     agent_port=14268,
    # )

    main_trace_exporter = OTLPSpanExporter(
        endpoint="http://172.18.0.3:4317"
    )

    tracer_provider.add_span_processor(
        # BatchSpanProcessor buffers spans and sends them in batches in a
        # background thread. The default parameters are sensible, but can be
        # tweaked to optimize your performance
        BatchSpanProcessor(main_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)

if __name__ == '__main__':

    setup_tracer("test-service-2")

    logs_list = []
    stream_handler = logging.StreamHandler(sys.stdout)

    LoggingInstrumentor().instrument()
    logger = logging.getLogger(__name__)
    logger.addHandler(stream_handler)
    logger.addHandler(RecordsListHandler(logs_list))
    logger.setLevel(logging.DEBUG)
    # logger.info("Test")


    tracer = trace.get_tracer('__name__')
    print(tracer)
    with tracer.start_as_current_span("test") as sp:
        logging.info("Logging info")
        logger.info( sp.get_span_context().trace_id )
        # logger.info("log-list")
        # print(logs_list)
        now = datetime.now()
        print("Current Time =", now.strftime("%H:%M:%S"))
