import time
from typing import Any, Dict, Optional

import requests

from src.config import Settings
from src.core.exceptions import HTTPException, HTTPExceptionType
from src.core.interfaces import ILogger


class BaseApiAdapter:
    """Base class for external API adapters with common HTTP functionality."""

    def __init__(
        self,
        logger: ILogger,
        settings: Settings,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the base API adapter.

        Args:
            logger: Logger instance
            settings: Application settings
            base_url: Base URL for the API
            headers: Default headers to include in all requests
        """
        self.logger = logger
        self.settings = settings
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    async def _make_request(
        self,
        method: str,
        endpoint: str = "",
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        handle_busy_response: bool = False,
    ) -> Dict[str, Any] | None:
        """
        Make HTTP request to API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            json_data: JSON data for request body
            params: Query parameters
            headers: Additional headers
            handle_busy_response: Whether to handle "busy" responses specially

        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        request_kwargs = {"json": json_data, "params": params, "headers": headers}

        # remove None values
        request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}

        retries = 0
        last_exception = None

        while retries < self.settings.EXTERNAL_MAX_RETRIES:
            try:
                response = self.session.request(method, url, **request_kwargs)

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=requests.codes.not_found,
                        detail=HTTPExceptionType.ResourceNotFound.value,
                    )

                if response.status_code != 200:
                    if handle_busy_response and "busy" in str(response.text).lower():
                        raise HTTPException(
                            status_code=requests.codes.service_unavailable,
                            detail=HTTPExceptionType.ServiceUnavailable.value,
                        )

                    raise Exception(
                        f"Error in {method} request to {url}: {response.status_code} - {response.text}"
                    )

                return response.json()

            except Exception as e:
                last_exception = e
                retries += 1
                self.logger.warn(
                    f"{str(e)} (attempt {retries}/{self.settings.EXTERNAL_MAX_RETRIES}). Retrying..."
                )

                if retries < self.settings.EXTERNAL_MAX_RETRIES:
                    time.sleep(self.settings.EXTERNAL_RETRY_DELAY_SECONDS)
                else:
                    raise e from last_exception

    async def get(self, endpoint: str = "", **kwargs) -> Dict[str, Any] | None:
        """Make GET request."""
        return await self._make_request("GET", endpoint, **kwargs)

    async def post(
        self,
        endpoint: str = "",
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any] | None:
        """Make POST request with JSON data."""
        return await self._make_request("POST", endpoint, json_data=json_data, **kwargs)

    def close(self) -> None:
        """Close the session."""
        self.session.close()
