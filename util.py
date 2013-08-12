from rdflib import plugin
from rdflib.namespace import Namespace
from rdflib.graph import Dataset
from rdflib.plugins.stores.sparqlstore import SPARQLStore

ns_dict = {
    'NP': 'http://www.nanopub.org/nschema#',
    'RSA': 'http://rdf.biosemantics.org/ontologies/rsa#',
    'HG19': 'http://rdf.biosemantics.org/data/genomeassemblies/hg19#',
    'PAV': 'http://swan.mindinformatics.org/ontologies/1.2/pav/',
    'SIO': 'http://semanticscience.org/resource/',
    'xsd': 'http://www.w3.org/2001/XMLSchema#',
    'DC': 'http://purl.org/dc/terms/',
    'SO': 'http://purl.org/obo/owl/SO#',
    'OBO': 'http://purl.org/obo/owl/obo#',
    'PROV': 'http://www.w3.org/ns/prov#',
    'GDA': 'http://rdf.biosemantics.org/dataset/gene_disease_associations#',
    'FANTOM5': 'http://rdf.biosemantics.org/data/riken/fantom5/data#',
    'RID': 'http://www.researcherid.com/rid/',
    'TM': 'http://rdf.biosemantics.org/vocabularies/text_mining#'
}


def bind_namespaces(graph, base_context):
    for key, value in ns_dict.items():
        graph.bind(key.lower(), value)
    graph.bind(None, base_context + '#')


class NanoPubTripleStore(object):

    RSA = Namespace(ns_dict['RSA'])
    HG19 = Namespace(ns_dict['HG19'])
    NP = Namespace(ns_dict['NP'])

    def __init__(self, endpoint):
        self.store = SPARQLStore(endpoint)
        self.dataset = Dataset()

    def _get_resources_by_context(self, context):
        g = self.dataset.graph(context)
        results = self.store.query("select ?s ?p ?o where {GRAPH <%s> {?s ?p ?o}}" % context)
        for s, p, o in results:
            self.dataset.add_quad((s, p, o, g))

    def get_nanopub(self, base):
        self._get_resources_by_context(base)
        self._get_resources_by_context(base + '#assertion')
        self._get_resources_by_context(base + '#publicationInfo')
        self._get_resources_by_context(base + '#provenance')
        bind_namespaces(self.dataset, base)
        return self.dataset.serialize(base=base, format='trig')


class Fantom5NanoPubTripleStore(NanoPubTripleStore):

    def get_cage_clusters(self, request):

        chromosome = request.args.get('chr', 'chr1')
        start = request.args.get('start', None)
        end = request.args.get('end', None)
        orientation = request.args.get('orientation', 'both')

        select_list = ["?cluster", "?loc", "?np", "?start", "?end", "?type"]
        where_list = ["?loc rsa:start ?start; rsa:end ?end; rsa:regionOf hg19:%s" % chromosome,
                      "?cluster rsa:mapsTo ?loc; rsa:type ?type"]
        filter_list = []

        if orientation != 'both':
            where_list.append("?loc rsa:hasOrientation rsa:%s" % orientation)
        else:
            where_list.append("?loc rsa:hasOrientation ?orientation")
            select_list.append("?orientation")

        if start:
            filter_list.append("?start > %s" % start)
        if end:
            filter_list.append("?end < %s" % end)

        q = """
        select %s
        where {
            ?np np:hasAssertion ?graph .
            GRAPH ?graph {
                %s
            }
            %s
        }""" % (" ".join(select_list), " . \n".join(where_list),
                "filter(%s)" % (" && ".join(filter_list) if filter_list else ""))

        return q, []  # TODO: self.store.query(q)

