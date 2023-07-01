from typing import Literal, Optional

from ..exceptions import *

PROXY_TYPE_SOCKS4 = SOCKS4 = 1
PROXY_TYPE_SOCKS5 = SOCKS5 = 2
PROXY_TYPE_HTTP = HTTP = 3

SearchFilter = Literal["Latest", "users", "photos", "videos"]


class Proxy:
    def __init__(
        self,
        host: str,
        port: int,
        proxy_type: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host
        self.password = password
        self.proxy_type = proxy_type
        self.username = username
        self.port = port
        self.proxy = self.__parse__()

    def __proxy_url__(self):
        if self.username and self.password:
            return "{}:{}@{}:{}".format(
                self.username, self.password, self.host, self.password
            )
        else:
            return "{}:{}".format(self.host, self.password)

    def __parse__(self):
        proxy_url = self.__proxy_url__()
        if self.proxy_type == HTTP:
            return dict(http=proxy_url, https=proxy_url)
        elif self.proxy_type == SOCKS4:
            socks_url = "socks4://{}".format(proxy_url)
            return dict(http=socks_url, https=socks_url)
        elif self.proxy_type == SOCKS5:
            socks_url = "socks5://{}".format(proxy_url)
            return dict(http=socks_url, https=socks_url)

        raise ProxyParseError()


class GenericError:
    EXCEPTIONS = {32: InvalidCredentials, 144: InvalidTweetIdentifier}

    def __init__(self, response, error_code, message=None):
        self.response = response
        self.error_code = error_code
        self.message = message
        self._raise_exception()

    def _raise_exception(self):
        if self.EXCEPTIONS.get(self.error_code):
            raise self.EXCEPTIONS[self.error_code](
                error_code=self.error_code,
                error_name=TWITTER_ERRORS[self.error_code],
                response=self.response,
            )

        raise UnknownError(
            error_code=self.error_code,
            error_name=TWITTER_ERRORS[self.error_code],
            response=self.response,
            message="[{}] {}".format(self.error_code, self.message),
        )
