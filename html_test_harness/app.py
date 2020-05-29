import json
from flask import Flask, render_template, request, Response

from html_test_harness.domain import Domain
from html_test_harness.domain_store import DomainStore
from html_test_harness.url_for import URLFor

app = Flask(__name__)


def get_domains():
    domain_store = DomainStore()

    domains = []
    domains_by_url = {}
    count = 0

    for domain in domain_store:
        if not domain.is_valid:
            continue

        if count < 100:
            domains.append(domain)

        count += 1

        domains_by_url[domain.url] = domain

    return domains, domains_by_url


def _sort_domains(domains, comments):
    if not comments:
        return domains

    def _key(domain):
        if domain.name not in comments:
            return 3, None

        comment = comments[domain.name].lower()
        if 'bust' in comment:
            return 0, comment

        if 'usable' in comment:
            return 1, comment

        return 2, comment

    return sorted(domains, key=_key)


DOMAINS, DOMAINS_BY_URL = get_domains()


@app.route('/')
def list():
    try:
        with open('comments.json') as handle:
            comments = json.load(handle)

        domains = _sort_domains(DOMAINS, comments)

    except FileNotFoundError:
        comments = {}
        domains = DOMAINS

    return render_template(
        'list.html.jinja2',
        domains=domains,
        url_for=URLFor,
        comments=comments,
    )


@app.route('/proxy')
def proxy_example():
    url = request.args['url']
    domain = DOMAINS_BY_URL[url]

    original = domain.response

    return Response(
        original.content,
        status=200,
        #headers=dict(original.headers),
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