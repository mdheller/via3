from urllib.parse import urlparse, urlencode
import json
from flask import Flask, render_template, request

from html_test_harness.domain_store import DomainStore
from html_test_harness.domain import Domain

app = Flask(__name__)


def get_domains():
    domain_store = DomainStore()

    domains = []
    domains_by_url = {}
    count = 0

    for domain in domain_store:
        if not domain.is_valid:
            continue

        if count > 100:
            break
        count += 1

        domains.append(domain)
        domains_by_url[domain.url] = domain

    return domains, domains_by_url


DOMAINS, DOMAINS_BY_URL = get_domains()


def url_for(link, rewriter):
    url = urlparse('http://localhost:9083/html')
    url = url._replace(query=urlencode({'url': link, 'via.rewriter': rewriter}))

    return url.geturl()


def legacy_url_for(link):
    return f'http://localhost:9080/{link}'


@app.route('/')
def list():
    try:
        with open('comments.json') as handle:
            comments = json.load(handle)
    except FileNotFoundError:
        comments = {}

    return render_template(
        'list.html.jinja2',
        domains=DOMAINS,
        url_for=url_for,
        legacy_url_for=legacy_url_for,
        comments=comments,
    )


@app.route('/save_comments', methods=["POST"])
def save_comments():
    comments = {}

    for name, value in request.form.items():
        _, domain = name.split('|', 1)
        comments[domain] = value

    with open('comments.json', 'w') as handle:
        json.dump(comments, handle)

    return list()

if __name__ == '__main__':
    app.run(debug=True)