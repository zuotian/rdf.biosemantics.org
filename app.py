"""
@organization: Leiden University Medical Center (LUMC)
@author: Zuotian Tatum
@contact: z.tatum@lumc.nl
"""
import os
from urllib import quote
from werkzeug.datastructures import Headers

from flask import Flask, Response, request
from flask.helpers import send_from_directory
from flask.templating import render_template
from filters import predicate, strand
from util import NanoPubTripleStore, Fantom5NanoPubTripleStore

app = Flask(__name__)
app.debug = True
app.config['cwd'] = os.path.dirname(__file__)
app.config.from_pyfile('./app.cfg')


app.jinja_env.filters['predicate'] = predicate
app.jinja_env.filters['strand'] = strand
app.jinja_env.filters['quote'] = quote


def mimetype_response(current_response, content_type=None):
    if not content_type and request.accept_mimetypes['text/html-rdf']:
        from lib.sw_lexer import Notation3Lexer
        from pygments import highlight
        from pygments.formatters.html import HtmlFormatter

        return highlight(current_response, Notation3Lexer(), HtmlFormatter())

    return Response(response=current_response, content_type=content_type)


################################ app url routing #######################################################################

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/<string:category>/<path:filename>')
def handle_file(category, filename):
    return send_from_directory(os.path.join(app.config['cwd'], category), filename, mimetype='text/plain;charset=utf-8')


@app.route("/nanopubs/<string:catalog>/<string:subtype>/<string:nanopub_id>", methods=['GET', 'POST'])
def get_nanopub(catalog, subtype, nanopub_id):
    if catalog == 'riken-fantom5':
        return mimetype_response("This project is currently under password protection. "
                                 "Please visit http://agraph.biosemantics.org, and log in to view data.",
                                 content_type='text/plain; charset=utf-8')
    base = "/".join([app.config['NANOPUB_CONTEXT'], catalog, subtype, nanopub_id])
    nanopub_store = NanoPubTripleStore(app.config['ENDPOINTS'][subtype])
    return mimetype_response(nanopub_store.get_nanopub(base))


@app.route("/query/nanopubs", methods=['GET'])
def query_nanopubs():
    # TODO: use limit and offset for query.
    store = request.args.get('store', '').lower()
    rows = []
    context = {
        'error': '',
        'track_url': "%sgenerate_track?%s" % (request.host_url, request.query_string)
    }
    endpoint = Fantom5NanoPubTripleStore(app.config['ENDPOINTS'][store])
    if store == 'riken_fantom5_cage_clusters':
        q, rows = endpoint.get_cage_clusters(request)
    else:
        context['error'] = "Please select a valid store."
        q = None
    return render_template('query_result.html', q=q, rows=rows, **context)


@app.route("/generate_track")
def generate_track():
    store = request.args.get('store', '')
    endpoint = Fantom5NanoPubTripleStore(app.config['ENDPOINTS'][store])
    context = {}
    if store == 'RIKEN_FANTOM5_CAGE_CLUSTERS':
        q, rows = endpoint.get_cage_clusters(request)
        context['track_name'] = "FANTOM5 CAGE"
        context['track_description'] = 'FANTOM5 CAGE Clusters on %s' % request.args.get('chr', 'chr1')
        context['track_url'] = '%snanopubs/riken/fantom5/cage_clusters/' % request.host_url
        context['track_htmlurl'] = '%sdata/riken/fantom5/ucsc.html' % request.host_url
    else:
        raise ValueError("Please select a valid store.")

    headers = Headers()
    headers.add('Content-Type', 'text/plain; charset=utf-8')

    if request.args.get('action', '') == 'download':
        headers.add('Content-Disposition', 'attachment', filename='test.bed')

    return Response(response=render_template('query_result.bed', rows=rows, **context), headers=headers)


if __name__ == "__main__":
    app.run()
