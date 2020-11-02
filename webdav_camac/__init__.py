from functools import partial
from http.cookies import SimpleCookie

from wsgidav.middleware import BaseMiddleware


def set_cookie(start_response, status, headers, exc_info=None):
    cookie = SimpleCookie()
    cookie["session"] = "this_session"
    # TODO make cookie secure, maybe this:
    # cookie["session"]["secure"] = True
    # cookie["session"]["httponly"] = True
    headers.append(str(cookie).split(": "))
    return start_response(status, headers, exc_info)


class CamacAuthenticator(BaseMiddleware):
    def __call__(self, environ, start_response):
        print("hello middleware")

        if "HTTP_COOKIE" in environ:
            cookie = SimpleCookie(environ["HTTP_COOKIE"])
            if "session" in cookie:
                print("Sucess, cookie was stored")
                return self.next_app(environ, start_response)

        return self.next_app(environ, partial(set_cookie, start_response))
