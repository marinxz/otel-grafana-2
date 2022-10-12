from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

def build_trace_contect( carrier_dir ):
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier_dir)
    if ctx:
        return ctx
    else:
        return None


def get_current_formated_traceparent():
    carrier = {}
    # Write the current context into the carrier.
    TraceContextTextMapPropagator().inject(carrier)
    if 'traceparent' in carrier:
        return carrier['traceparent']
    else:
        return None

    