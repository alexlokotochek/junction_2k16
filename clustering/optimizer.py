from metagraph import *
from utils import *
import louvain
import numpy as np
import copy
from collections import namedtuple

class Optimizer:
    SMG = None

    session_to_products = {}
    total_users_number = None
    backup_session_to_products = {}
    consider_comms_grid = None # example: range(2, 5)
    resolution_parameter_grid = None # example: list(np.arange(1.0, 300.0, 0.1))

    P_THRESHOLD = 0.75

    tfidf_types_grid = ['simple', 'sqrt', 'max', 'neighbours']
    already_tested = {}

    best_partition, results = [], []

    # Set from __init__ parameters
    basic_bound = 0
    current_tfidf_type = 'sqrt'


    def __init__(self,
                 coviews,
                 test_sessions_,
                 basic_bound=0,
                 tfidf_type='sqrt',
                 how='new',
                 SMG=None,
                 consider_comms_grid=range(2,5),
                 resolution_parameter_grid=list(np.arange(1.0, 300.0, 0.1))):
        self.consider_comms_grid = consider_comms_grid
        self.resolution_parameter_grid = resolution_parameter_grid
        self.session_to_products = copy.copy(test_sessions_)
        self.backup_session_to_products = copy.copy(test_sessions_)
        self.current_tfidf_type = tfidf_type
        self.basic_bound = basic_bound
        print('sessions in test:', len(self.session_to_products.items()))
        self.total_users_number = len(self.session_to_products.items())
        if how == 'read':
            print('restoring metagraph from previous state...')
            self.SMG = SMG
        elif how == 'new':
            print('building graph...')
            self.SMG = Metagraph(coviews, basic_bound)
            print('counting weights...')
            self.SMG._count_weights(tfidf_type=self.current_tfidf_type)
        self.current_tfidf_type = tfidf_type
        print('vertices:', len(self.SMG.g.vs))


    def _clusterized_products(self,
                              partition,
                              num_to_prod):
        clusterized_products = set([])
        for part in partition:
            for product in part:
                clusterized_products |= set([num_to_prod[product]])
        return clusterized_products


    def _correct_test_sessions(self,
                               products_clusterized):
        for stp in list(self.session_to_products.items()):
            for product in list(stp[1]):
                if product not in products_clusterized:
                    self.session_to_products[stp[0]] -= set([product])
        for stp in list(self.session_to_products.items()):
            if len(stp[1]) <= 1:
                del self.session_to_products[stp[0]]


    def _count_metrics(self,
                      partition,
                      num_to_prod):
        self.session_to_products = copy.copy(self.backup_session_to_products)
        prod_to_cluster = {}
        for i, cluster in enumerate(partition):
            for prod in cluster:
                prod_to_cluster[num_to_prod[prod]] = i
        clusterized_products = self._clusterized_products(partition,
                                                          num_to_prod)
        self._correct_test_sessions(clusterized_products)

        good_count, \
        user_count, \
        total_clusters_scores = self._count_users_clusters_distrubution(partition,
                                                                       prod_to_cluster)

        more_than = self._analyze_clusters(partition)
        quality = good_count*more_than.edge*1./(user_count\
                                           *len(partition)\
                                           *np.log(max(total_clusters_scores.values())\
                                                  +len(partition)\
                                                  +max([len(cluster) for cluster in partition])))
        return quality, total_clusters_scores


    def _count_users_clusters_distrubution(self,
                                           partition,
                                           prod_to_cluster):
        total_clusters_scores, clusters_scores = {}, {}
        good_count, user_count = 0, 0
        for i in range(len(partition)):
            total_clusters_scores[i] = 0
        for user in self.session_to_products.keys():
            clust_value_counts = {}
            for i in range(len(partition)):
                clust_value_counts[i] = 0
            for viewed_product in self.session_to_products[user]:
                if viewed_product in prod_to_cluster:
                    clust_value_counts[prod_to_cluster[viewed_product]] += 1
            norm = np.sum(clust_value_counts.values())*1.
            if norm == 0.:
                continue
            user_count += 1
            cluster_number = -1
            for i, score in enumerate(clust_value_counts.values()):
                if score > self.P_THRESHOLD * norm:
                    cluster_number = i
            if cluster_number != -1:
                good_count += 1
                if cluster_number not in clusters_scores:
                    clusters_scores[cluster_number] = 0
                clusters_scores[cluster_number] += 1
                total_clusters_scores[cluster_number] += 1
        return good_count, user_count, total_clusters_scores


    def _analyze_clusters(self,
                          partition,
                          silent=False):
        Cluster_info = namedtuple('Cluster_info', 'triangle edge vertex')
        more_than = Cluster_info(triangle=sum([1 if len(cluster) > 3 else 0
                                               for cluster in partition]),
                                 edge=sum([1 if len(cluster) > 2 else 0
                                           for cluster in partition]),
                                 vertex=sum([1 if len(cluster) > 1 else 0
                                             for cluster in partition]))
        if not silent:
            print('clusters with len > 3:', more_than.triangle,
                  'clusters with len > 2:', more_than.edge,
                  'clusters with len > 1:', more_than.vertex)
        return more_than


    def _get_random_parameters(self):
        result = (-1,-1,-1)
        while (result in self.already_tested):
            result = (np.random.choice(self.consider_comms_grid),
                      np.random.choice(self.resolution_parameter_grid),
                      np.random.choice(self.tfidf_types_grid))
        self.already_tested[result] = True
        return result


    def optimize(self, attempts=500,
                 tfidf_axis=False,
                 straight_conditions=True,
                 return_top=1):
        results = []
        count = 0
        self.already_tested = {}
        self.already_tested[(-1,-1,-1)] = True
        while (count < attempts):
            if int(round(count*100./attempts)) % 10 == 0:
                print 'passed', int(count*100./attempts), '%...'
            cc, rp, tfidf_type_ = self._get_random_parameters()
            print '\ncc:', cc, '\trp:', rp
            if tfidf_axis:
                print 'tfidf_type:', tfidf_type_
            if tfidf_axis:
                self.SMG._count_weights(tfidf_type=tfidf_type_, silent=True)
            clusters = self._find_partition(cc, rp)
            quality, distribution = self._count_metrics(list(clusters),
                                                       self.SMG.num_to_product)
            if straight_conditions and not report_result:
                continue
            return_clusters = []
            for cl in clusters:
                this_cluster = [self.SMG.num_to_product[n] for n in cl]
                return_clusters.append(this_cluster)

            results.append((tfidf_type_,
                            self.basic_bound,
                            cc,
                            rp,
                            return_clusters,
                            distribution,
                            quality))
            count += 1
        print('passed')
        best = sorted(results, key=lambda tup:tup[-1], reverse=True)[:return_top]
        self.results = list(results)
        return best


    def _find_partition(self, cc, rp):
        partition = louvain.find_partition(self.SMG.g,
                                           method='RBConfiguration',
                                           weight='weight',
                                           consider_comms=cc,
                                           resolution_parameter=rp)
        return [list(p) for p in partition]
