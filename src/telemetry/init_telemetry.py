from os import environ
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


def setup_tracer(service_name, app_name, tempo_host):
    """
    This one will try to set up tracer depending on the JAEGER_HOST
    if that one is not present not defined it presumes it is are operating
    in the cloud
    :param service_name:
    :return:
    """
    resource = Resource.create({SERVICE_NAME: service_name, 'app':app_name })
    tracer_provider = TracerProvider(resource=resource)

    main_trace_exporter = OTLPSpanExporter(
        # endpoint="http://" + tempo_host + ":4317"
        endpoint="http://" + tempo_host + ":4318" + "/v1/traces"

    )

    tracer_provider.add_span_processor(
        # BatchSpanProcessor buffers spans and sends them in batches in a
        # background thread. The default parameters are sensible, but can be
        # tweaked to optimize your performance
        BatchSpanProcessor(main_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)


def init_telemetry_fastapi(service_name, app_name, tempo_host):
    setup_tracer(service_name, app_name, tempo_host)


def init_telemetry_celery(service_name, app_name, tempo_host):
    setup_tracer(service_name, app_name, tempo_host )

