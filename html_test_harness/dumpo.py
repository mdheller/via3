from html_test_harness.domain import Domain

from html_test_harness.domain_store import DomainStore

import hashlib

def name(url):


for domain in DomainStore():
    if not domain.is_valid:
        continue

    print(domain.url)
    hash = hashlib.md5()
    hash.update(domain.url.encode('utf-8'))
    filename = hash.hexdigest() + '.html'

    with open("hexdump/" + filename, 'wb') as handle:
        handle.write(domain.response.content)
