from prometheus_client import Counter, Gauge, generate_latest, CollectorRegistry
import time

class Metrics:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.counters = {}
        self.gauges = {}
        # common counters
        self._get_counter("requests_total")
        self._get_counter("worker_tasks_total")
        self._get_counter("worker_heartbeat_total")
        self._get_counter("worker_errors_total")
        self._get_gauge("last_request_success")

    def _get_counter(self, name):
        if name not in self.counters:
            self.counters[name] = Counter(name, name, registry=self.registry)
        return self.counters[name]

    def _get_gauge(self, name):
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, name, registry=self.registry)
        return self.gauges[name]

    def inc_counter(self, name, amt=1):
        self._get_counter(name).inc(amt)

    def set_gauge(self, name, value):
        self._get_gauge(name).set(value)

    def metrics_response(self):
        return generate_latest(self.registry)
