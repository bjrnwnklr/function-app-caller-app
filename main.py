import logging
import os

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


def get_request(url: str, params: dict) -> str:
    """Send a get request to the URL specified.

    Args:
        url (str): URL to send GET request to.
        params (dict): Dictionary of query parameters.

    Returns:
        str: Text received with the response.
    """
    data = ""  # initialize so we always return a defined value
    try:
        response = requests.get(url, timeout=10, params=params)
        logger.info(f"Response status code: {response.status_code}")
        response.raise_for_status()
        data = response.text
        logger.info(f"Response from Function App: {data}")

    except Timeout:
        # Handle timeout specifically
        logger.error("Request timed out")

    except ConnectionError:
        # Handle connection issues (DNS failure, refused connection, etc.)
        logger.error("Connection failed")

    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors (4xx, 5xx)
        logger.error(f"HTTP error occurred: {e}")
        logger.error(f"Status code: {response.status_code}")

    except RequestException as e:
        # Catch-all for any other requests-related errors
        logger.error(f"Request failed: {e}")

    return data


def main():
    logger.info("Hello from the external-caller-app!")
    endpoint = "httpexample"
    url = URL_BASE + endpoint
    params = {"name": "Bjoern"}
    data = get_request(url, params)


if __name__ == "__main__":
    main()
