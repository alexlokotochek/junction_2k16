import numpy
import pandas as pd
import math


class Contain:

    def __init__(self, items):
        self.items = set(items)

    def __ne__(self, other):
        return other not in self.items

    def __eq__(self, other):
        return other in self.items
        

def is_nan(x):
    return isinstance(x, float) and math.isnan(x)


def count_popularity(edges_df):
    product_pop = {}
    for e in edges_df.values:
        if e[0] not in product_pop:
            product_pop[e[0]] = 0
        product_pop[e[0]] += e[2]
        if e[1] not in product_pop:
            product_pop[e[1]] = 0
        product_pop[e[1]] += e[2]
    return product_pop

def read_test_sessions(filename):
    test_sessions_df = pd.read_csv(filename, sep='\t').dropna()
    session_to_products = {}
    for ts in test_sessions_df.values:
        session = ts[0]
        if session not in session_to_products:
            session_to_products[session] = set([])
        session_to_products[session] |= set([ts[1]])
    return session_to_products


def load_clusters(filename):
    f = open(filename, "r")
    clusters = []
    s = f.readline()
    while s:
        cnt = s.count(' ')
        cluster_str = ()
        cluster = []
        cluster_str = s.split(' ', cnt)
        for string in cluster_str:
            node = int(string)
            cluster.append(node)
        clusters.append(cluster)
        s = f.readline()
    f.close()
    return clusters


def load_product_metainf(filename):
    product_prices_df = pd.read_csv(filename, sep='|')[['product_id','name','price']]
    product_price = {}
    product_name = {}
    for pp in product_prices_df.values:
        product_price[pp[0]] = pp[2]
        product_name[pp[0]] = pp[1]
    return product_price, product_name