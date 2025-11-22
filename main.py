import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Optional

import requests
from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from requests.exceptions import RequestException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name=__name__)


class FunctionAppClient:
    # client for authenticating and calling Azure Function App

    def __init__(self):
        logger.debug("Initializing FunctionAppClient")
        load_dotenv()
        self.env = os.getenv("CALLER_APP_ENV")
        # adjust based on whether we run the function app locally or on Azure
        self.url_base = (
            os.getenv("CALLER_APP_URL_BASE_LOCAL")
            if self.env == "LOCAL"
            else os.getenv("CALLER_APP_URL_BASE_AZURE")
        )

        function_app_client_id = os.getenv("AZURE_FUNCTION_APP_CLIENT_ID")

        self.scope = f"api://{function_app_client_id}/.default"

        # initiate credential
        self._credential = DefaultAzureCredential()

        # token caching
        self._token_expiry_buffer = timedelta(minutes=5)
        self._cached_token: Optional[AccessToken] = None

        logger.debug(f"Function App URL is {self.env}: {self.url_base}")

    def _get_access_token(self) -> str:
        """Get access token, using cached token if not expired.

        Returns:
            str: Azure Access Token
        """
        now = datetime.now().timestamp()

        # use cached token if it exists in the token cache and is
        # not within expiration buffer
        if (
            self._cached_token
            and self._token_expiry_buffer.total_seconds()
            < self._cached_token.expires_on - now
        ):
            logger.debug("Using cached token")
            return self._cached_token.token

        # token has expired, request a new one
        logger.debug("Aquiring new token")
        self._cached_token = self._credential.get_token(self.scope)

        return self._cached_token.token

    def _get_auth_header(self) -> dict:
        """Generates authentication header with a bearer token.

        Returns:
            dict: Authentication header with a Bearer token.
        """
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }
        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """
        Make HTTP request to Function App.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json: JSON body for POST/PUT requests
            timeout: Request timeout in seconds

        Returns:
            requests.Response object

        Raises:
            RequestException: For any request-related errors
        """
        url = f"{self.url_base}/{endpoint}"
        headers = self._get_auth_header()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params or {},
                json=json,
                timeout=timeout,
            )

            logger.debug(f"{method} {endpoint}: {response.status_code}")
            response.raise_for_status()

            return response

        except requests.exceptions.Timeout:
            logger.error(f"Request to {endpoint} timed out after {timeout}s")
            raise

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed for {endpoint}: {e}")
            raise

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP {e.response.status_code} error for {endpoint}: {e.response.text}"
            )
            raise

        except RequestException as e:
            logger.error(f"Request to {endpoint} failed: {e}")
            raise

    def get(
        self, endpoint: str, params: Optional[dict] = None, **kwargs
    ) -> requests.Response:
        """Send GET request to the function app.

        Args:
            endpoint (str): API endpoint
            params (Optional[dict], optional): HTTP Request parameters. Defaults to None.

        Returns:
            requests.Response: Response from the endpoint.
        """
        return self._make_request("GET", endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        payload: Optional[dict] = None,
        params: Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        """Send POST request to the function app.

        Args:
            endpoint (str): API endpoint
            payload (Optional[dict], optional): JSON payload. Defaults to None.
            params (Optional[dict], optional): HTTP Request paramters. Defaults to None.

        Returns:
            requests.Response: Response from the endpoint.
        """
        return self._make_request(
            "POST", endpoint, params=params, json=payload, **kwargs
        )


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
    # create FunctionAppClient instance
    client = FunctionAppClient()

    try:
        # check if the function app is alive
        logger.info("Checking alive status of the function app")
        response = client.get("alive")
        logger.info(f"Alive check: {response.status_code} {response.text}")

        # send numbers and see what comes back.
        n = 10000
        m = 2000
        digits = 5
        logger.info(
            f"GET request to 'process_numbers': {n} numbers to match against {m} numbers, {digits} digits."
        )
        numbers = create_numbers(n, digits=digits)
        payload = {"numbers": numbers, "numbers_to_compare": m, "digits": digits}
        # print size of payload
        json_bytes = len(json.dumps(payload).encode("utf-8"))
        json_mbytes = json_bytes / 1024**2
        logger.info(f"Size of the payload in MB: {json_mbytes:.4f}")
        # call the API
        response = client.post("process_numbers", payload=payload)

        # get json object of response
        response_payload = json.loads(response.text)

        logger.info(
            f"Process Numbers: {response.status_code} {response_payload['count']}"
        )
    except RequestException as e:
        logger.error(f"Request failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
