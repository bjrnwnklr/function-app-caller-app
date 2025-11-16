import logging
import os
import random

import requests
from dotenv import load_dotenv
from requests.exceptions import ConnectionError, RequestException, Timeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name=__name__)

# load URL BASE from .env file
load_dotenv()
CALLER_APP_ENV = os.getenv("CALLER_APP_ENV")
# adjust based on whether we run the function app locally or on Azure
URL_BASE = (
    os.getenv("CALLER_APP_URL_BASE_LOCAL")
    if CALLER_APP_ENV == "LOCAL"
    else os.getenv("CALLER_APP_URL_BASE_AZURE")
)
logger.info(f"Function App URL is {CALLER_APP_ENV}: {URL_BASE}")


def get_request(url: str, params: dict) -> requests.Response:
    """Send a get request to the URL specified.

    Args:
        url (str): URL to send GET request to.
        params (dict): Dictionary of query parameters.

    Returns:
        requests.Response: Response object received
    """
    fallback = requests.Response()  # ensure we always return a Response object
    try:
        resp = requests.get(url, timeout=10, params=params)
        logger.debug(f"Response status code: {resp.status_code}")
        resp.raise_for_status()
        logger.debug(f"Response text from Function App: {resp.text}")
        return resp

    except Timeout:
        # Handle timeout specifically
        logger.error("Request timed out")
        fallback.status_code = 408
        fallback._content = b"Request timed out"
        return fallback

    except ConnectionError:
        # Handle connection issues (DNS failure, refused connection, etc.)
        logger.error("Connection failed")
        fallback.status_code = 503
        fallback._content = b"Connection failed"
        return fallback

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (4xx, 5xx)
        logger.error(f"HTTP error occurred: {e}")
        # Prefer the original response if available on the exception
        if hasattr(e, "response") and e.response is not None:
            return e.response
        # otherwise return fallback populated with error info
        fallback.status_code = (
            getattr(e.response, "status_code", 500) if hasattr(e, "response") else 500
        )
        fallback._content = str(e).encode()
        return fallback

    except RequestException as e:
        # Catch-all for any other requests-related errors
        logger.error(f"Request failed: {e}")
        fallback.status_code = 400
        fallback._content = str(e).encode()
        return fallback


def post_request(url: str, payload: dict, params: dict) -> requests.Response:
    """Send a post request to the provided URL.

    Args:
        url (str): URL endpoint to call
        payload (dict): dictionary to send as body of the POST request.
            Will be converted to JSON as part of the POST request.
        params (dict): Dictionary of parameters to send.

    Returns:
        requests.Response: requests.Response object with the
          response received
    """
    fallback = requests.Response()  # ensure we always return a Response object
    try:
        resp = requests.post(url, json=payload, timeout=10, params=params)
        logger.debug(f"Response status code: {resp.status_code}")
        resp.raise_for_status()
        logger.debug(f"Response text from Function App: {resp.text}")
        return resp

    except Timeout:
        # Handle timeout specifically
        logger.error("Request timed out")
        fallback.status_code = 408
        fallback._content = b"Request timed out"
        return fallback

    except ConnectionError:
        # Handle connection issues (DNS failure, refused connection, etc.)
        logger.error("Connection failed")
        fallback.status_code = 503
        fallback._content = b"Connection failed"
        return fallback

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (4xx, 5xx)
        logger.error(f"HTTP error occurred: {e}")
        # Prefer the original response if available on the exception
        if hasattr(e, "response") and e.response is not None:
            return e.response
        # otherwise return fallback populated with error info
        fallback.status_code = (
            getattr(e.response, "status_code", 500) if hasattr(e, "response") else 500
        )
        fallback._content = str(e).encode()
        return fallback

    except RequestException as e:
        # Catch-all for any other requests-related errors
        logger.error(f"Request failed: {e}")
        fallback.status_code = 400
        fallback._content = str(e).encode()
        return fallback


def create_numbers(n: int = 10, digits: int = 8) -> list[int]:
    """Create a random list of numbers.

    Args:
        n (int): How many numbers to create.
        digits (int): Number of digits of each number

    Returns:
        list[int]: list of numbers
    """
    # create a random list of numbers
    numbers = [random.randint(0, int("1" + digits * "0")) for _ in range(n)]
    logger.debug(f"Created {len(numbers)} random numbers, first number: {numbers[0]}")
    return numbers


def main():
    # check if the function app is alive
    logger.info("Checking alive status of the function app")
    endpoint = "alive"
    url = URL_BASE + endpoint
    params = {}
    data = get_request(url, params)
    logger.info(f"Received response: {data.status_code} {data.text}")

    # send numbers and see what comes back.
    logger.info("Sending some numbers")
    numbers = create_numbers()
    endpoint = "process_numbers"
    url = URL_BASE + endpoint
    params = {}
    payload = {"numbers": numbers}
    resp = post_request(url, payload=payload, params=params)
    logger.info(f"Received response: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    main()
