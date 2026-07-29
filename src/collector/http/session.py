from uuid import uuid4


class HttpSession:
    def __init__(
        self, 
        application: str, 
        user_agent: str,
        accept: str,
        accept_language: str,
        referer: str
    ):
        self.__application = application
        self.__user_agent = user_agent
        self.__accept = accept
        self.__accept_language = accept_language
        self.__referer = referer
        self.__cookies = {}
        self.__clearance = None
        self.__request_id = str(uuid4())


    def build_headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": f"{self.__application}/{self.__user_agent}/{uuid4()}",
            "X-Request-Id": self.__request_id,
            "Accept": self.__accept,
            "Accept-Language": self.__accept_language,            
            "Referer": self.__referer
        }
            
        if self.__cookies:
            headers['Cookie'] = "; ".join(f"{k}={v}" for k, v in self.__cookies.items())
                
        return headers

    def update_cookie(self, name: str, value: str) -> None:
        self.__cookies[name] = value

    def clear_cookie(self) -> None:
        self.__cookies.clear()
            
    def update_clearance(self, name: str, value: str) -> None:
        self.__clearance[name] = value
            
    