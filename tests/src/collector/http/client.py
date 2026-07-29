import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from collector.core.exceptions import HttpRetryException
from collector.core.logging import get_logger
from collector.http.http import Http
from collector.http.models import HttpOptions, HttpRequest, HttpResponse
from collector.http.session import HttpSession


class HttpClient(Http):
    def __init__(self, options: HttpOptions, session: HttpSession):
        self.__logger = get_logger(__name__)
        self.__options = options
        self.__session = session
        self.__client = httpx.Client(
            timeout=options.timeout,
            verify=options.verify_tls,
            follow_redirects=options.follow_redirects,
            proxy=options.proxy
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((httpx.TransportError,HttpRetryException)),
        reraise=True
    )    
    def _request(self, request: HttpRequest) -> httpx.Response:
        self.__logger.info("http.request", method=request.method, url=request.url)
        
        response = self.__client.request(
            method=request.method,
            url=request.url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers={
                **self.__session.build_headers(),
                **(request.headers or {})
            }
        )
        
        for cookie in response.cookies.jar:
            self.__session.update_cookie(
                cookie.name,
                cookie.value
            )

        if response.status_code == 429 or response.status_code >= 500:
            self.__logger.warning("http.retry", status=response.status_code, url=request.url)
            raise HttpRetryException()
        
        self.__logger.info(
            "http.response",
            method=request.method,
            url=request.url,
            status=response.status_code,
        )
        return HttpResponse(
            status_code=response.status_code,
            url=str(response.url),
            headers=dict(response.headers),
            content=response.content
        )
    
    
    def get(self, url: str, **kwargs) -> HttpResponse:
        return self._request( 
            HttpRequest(
                method="GET",
                url=url,
                **kwargs
            )
        )
            

    def post(self, url: str, **kwargs) -> HttpResponse:
        return self._request( 
            HttpRequest(
                method="POST",
                url=url,
                **kwargs
            )
        )
