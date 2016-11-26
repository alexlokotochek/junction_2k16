import numpy as np
import json
from itertools import product as iter_product
import snowballstemmer

stemmer = snowballstemmer.stemmer('english')

data_file = open('product_info.json')
product_info = json.load(data_file)
productid_to_vector = {}
productid_to_cat = {}
productid_to_name = {}
for productid, info in product_info.items():
	productid_to_vector[productid] = set(info['stemmed_name'].split(' '))
	productid_to_cat[productid] = info['categoryId']
	productid_to_name[productid] = info['name']


def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False

def cosine_similarity(v1, v2):
	# sets
	intersect = len(v1 & v2)
	if intersect > 0:
		return intersect*1./np.sqrt(len(v1)*len(v2))
	else:
		return 0.
	
def cosine_similarity_overlap(v1, v2):
	intersect = len(v1 & v2)
	for w1, w2 in iter_product(list(v1), list(v2)):
		if (w1 in w2 or w2 in w1) and w1 != w2:
			intersect += 0.5
	if intersect > 0:
		return intersect*1./np.sqrt(len(v1)*len(v2))
	else:
		return 0.


class SearchSuggester:

	def __init__(self, query):
		# tuple (productid, name)
		self.suggested_product = None
		self.suggested_category = None
		query = query.strip().lower()
		query_vec = set(stemmer.stemWords(query.split()))
		distances = [(productid, cosine_similarity_overlap(query_vec, product_vec)) for productid, product_vec in productid_to_vector.items()]
		top = sorted(distances, key=lambda tup:tup[1], reverse=True)[:20]
		if top[0][1] >= 0.7 and top[1][1]<top[0][1]*0.5 or productid_to_name[top[0][0]].lower()==query:
			productid, dist = top[0]
			self.suggested_product = (productid, productid_to_name[productid])

		category_score, pos = {}, 1
                if top[0][1] != 0.:
			for productid, dist in top:
				pos += 1
			cat = productid_to_cat[productid]
			if cat not in category_score:
				category_score[cat] = 0
			# NDCG-like
			category_score[cat] += 1./np.log(pos+1)
                if len(category_score.items()) == 0:
                    return
                top_cat = sorted(category_score.items(), key=lambda tup:tup[1], reverse=True)[0]
		if top_cat[1] > 0:
			self.suggested_category = top_cat[0]

#def main():
#	ss = SearchSuggester('fuck')
#	print('fuck you')
#       if ss.suggested_product:
#		print 'sp:', ss.suggested_product
#	if ss.suggested_category:
#		print 'sc:', ss.suggested_category

#if __name__ == '__main__':
#	main()
		
