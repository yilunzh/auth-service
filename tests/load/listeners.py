"""Locust event hooks for load test observability."""

import logging

from locust import events

logger = logging.getLogger(__name__)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Load test starting — target host: %s", environment.host)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    response = kwargs.get("response")
    if response is not None and response.status_code == 429:
        logger.debug("429 rate-limited: %s %s (%.0fms)", request_type, name, response_time)
