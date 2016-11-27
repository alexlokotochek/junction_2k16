from modules.utils import *
import igraph as ig
import numpy as np
import pandas as pd
from tqdm import tnrange as prange, tqdm_notebook as pbar

# TODO: singleton
class Metagraph:
    g = None
    vertices = set([])
    primary_weights = {}
    num_to_product, product_to_num = {}, {}
    coviews = None
    views_popularity = {}
    this_basic_bound = None

    current_tfidf_type = None


    def __init__(self,
                 coviews_,
                 basic_bound=0,
                 dir='./save/',
                 how='new',
        
        if how == 'new':
            print 'creating graph...'
            self.this_basic_bound = basic_bound
            self.coviews = coviews_[coviews_['count'] >= basic_bound]
            self.views_popularity = count_popularity(self.coviews)
            self._build_graph()
        if how == 'load':
            print 'loading graph...'
            self.g = ig.load(dir+basic_bound+'_'+restored_tfidf+'_threshold.gml')
            pw = pd.read_csv(dir+'primary_weights.csv',index_col=['Unnamed: 0'])
            for v in pw.values:
                e = v[0][1:-1].split(',')
                e = (int(e[0]), int(e[1]))
                self.primary_weights[e] = v[1]
            ptn = pd.read_csv(dir+'product_to_num.csv',index_col=['Unnamed: 0'])
            for v in ptn.values:
                self.product_to_num[v[0]] = v[1]
                self.num_to_product[v[1]] = v[0]
            vp = pd.read_csv(dir+'views_popularity.csv',index_col=['Unnamed: 0'])
            for v in vp.values:
                self.views_popularity[v[0]] = v[1]


    def _build_graph(self):
        self.g = ig.Graph(directed=False)
        print('processing vertices...')
        for w in self.coviews.values:
            self.vertices |= set([w[0], w[1]])
        self.vertices = list(self.vertices)
        self.g.add_vertices(len(self.vertices))
        self.g.vs["name"] = range(len(self.g.vs))
        print('enumerating vertices...')
        for i, it in enumerate(self.vertices):
            self.product_to_num[it] = i
            self.num_to_product[i] = it
        print('initializing iGraph object...')
        for w in pbar(self.coviews.values):
            e = (w[0], w[1])
            self.g.add_edge(self.product_to_num[e[0]], self.product_to_num[e[1]])
            self.primary_weights[e] = w[2]
        print('100% edges processed!')

    def _count_weights(self, tfidf_type='sqrt', silent=False):
        total_edges = len(self.primary_weights)
        step = int(total_edges / 10)
        for w in pbar(self.primary_weights.items()):
            e = (w[0][0], w[0][1])
            weight = 0.
            if tfidf_type == 'simple':
                weight = w[1]
            else:
                pop_1, pop_2 = self.views_popularity.get(e[0]), self.views_popularity.get(e[1])
                w_ = w[1]
                if not pop_1 or not pop_2:
                    w_, pop_1, pop_2 = 0., 1., 1.
                if tfidf_type == 'sqrt':
                    weight = w_*1./np.sqrt(pop_1 * pop_2)
                else:
                    print 'wrong tfidf_type!'
                    return
            self.g.es.find(_between=((self.product_to_num[e[0]],),
                                     (self.product_to_num[e[1]],)))['weight'] = weight
        self.g.es['weight'] = [float(x) if not str(x)=='None' else 0.
                               for x in self.g.es['weight']]
        self.current_tfidf_type = tfidf_type
