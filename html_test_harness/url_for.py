import hashlib
from urllib.parse import urlparse, urlencode


class URLFor:
    @classmethod
    def proxy_rewriter(cls, link, rewriter):
        return cls.rewriter(cls.nginx_proxy(link), rewriter)

    @classmethod
    def nginx_proxy(cls, link):
        hash = hashlib.md5()
        hash.update(link.encode('utf-8'))

        return f'http://localhost:9083/hexdump/{hash.hexdigest()}.html'

    @classmethod
    def test_harness_proxy(cls, link, host='127.0.0.1'):
        url = urlparse(f'http://{host}:5000/proxy')
        url = url._replace(
            query=urlencode({'url': link}))

        return url.geturl()

    @classmethod
    def rewriter(cls, link, rewriter):
        url = urlparse('http://localhost:9083/html')
        url = url._replace(
            query=urlencode({'url': link, 'via.rewriter': rewriter}))

        return url.geturl()

    @classmethod
    def legacy_via(cls, link):
        return f'http://localhost:9080/{link}'