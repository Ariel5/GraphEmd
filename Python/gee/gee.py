import numpy as np

def compute_euclidean_distances(X):
        """
        Computes pairwise distance between row vectors or matrices
        Parameters
        ----------
        X : array_like
            If ``dissimilarity=='precomputed'``, the input should be the
            dissimilarity matrix with shape (n_samples, n_samples). If
            ``dissimilarity=='euclidean'``, then the input should be 2d-array
            with shape (n_samples, n_features) or a 3d-array with shape
            (n_samples, n_features_1, n_features_2).
        Returns
        -------
        out : 2d-array, shape (n_samples, n_samples)
            A dissimilarity matrix based on Frobenous norms between pairs of
            matrices or vectors.
        """
        shape = X.shape
        n_samples = shape[0]

        if X.ndim == 2:
            order = 2
            axis = 1
        else:
            order = "fro"
            axis = (1, 2)

        out = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            out[i] = np.linalg.norm(X - X[i], axis=axis, ord=order)

        return out
class GraphEncoderEmbedding:
	"""
	Implementation of the graph encoder embedding proposed by Shen at al.
	"""
	def __init__(self, lap=False, n_nodes=None):
		self.lap=lap
		self.n_nodes = n_nodes


	def fit(self, X, y):
		"""
		Input
		X - An edge list of shape (n_edges, {2,3}) or an adjacency matrix of shape (n_nodes, n_nodes).
		y - Labels for each node in implied by X
		"""

		self.classes = np.unique(y)

		if X.ndim == 3:
			X = process_matrix(compute_euclidean_distances(X), scale=True, negate=True)

		a, b = X.shape

		if b == 2:
			X = np.vstack((X, np.ones(a)))
			b = 3

		if b == 3:
			if self.n_nodes is None:
				self.n_nodes = len(np.unique(np.concatenate((X[:, 0], X[:, 1]))))
			edge_list = True

		elif a == b:
			self.n_nodes = a
			edge_list = False

		self.W = np.zeros((self.n_nodes, len(self.classes)))
		self.encoder_embedding = np.zeros((self.n_nodes, len(self.classes)))

		for i, k in enumerate(self.classes):
			inds = np.where(y == k)[0]
			self.W[inds, i] = 1 / len(inds)

		if edge_list:
			self._fit_edge_list(X, y)
		else:
			self._fit_matrix(X, y)

		self.pinv = np.linalg.pinv(self.encoder_embedding)

		return self


	def _fit_matrix(self, X, y):
		for i in range(X.shape[0]):
			y1 = y[i]
			y1_index = int(np.where(self.classes == y1)[0][0])

			for j in range(X.shape[1]):
				y2 = y[j]
				edge_weight = X[i,j]

				y2_index = int(np.where(self.classes == y2)[0][0])

				self.encoder_embedding[i, y2_index] += edge_weight * self.W[j, y2_index]
				self.encoder_embedding[j, y1_index] += edge_weight * self.W[i, y1_index]


	def _fit_edge_list(self, X, y):
		for i, edge in enumerate(X):
			node1 = int(edge[0])
			node2 = int(edge[1])

			y1 = y[node1]
			y2 = y[node2]
			edge_weight = edge[2]

			y1_index = int(np.where(self.classes == y1)[0][0])
			y2_index = int(np.where(self.classes == y2)[0][0])

			self.encoder_embedding[node1, y2_index] += edge_weight * self.W[node2, y2_index]
			self.encoder_embedding[node2, y1_index] += edge_weight * self.W[node1, y1_index]


	def transform(self, X):
		"""
		returns OOS embedding of X. X must be shape (n_of_sample_nodes, n_in_sample_nodes)
		"""

		return X @ self.pinv.T

	def fit_transform(self, X, y):
		self.fit(X, y)
		return self.transform(X)



def process_matrix(dist_matrix, make_symmetric=False, scale=False, aug_diag=False, negate=False, min_=None, max_=None):
    if make_symmetric:
        dist_matrix = 0.5*(dist_matrix + dist_matrix.T)
        
    if negate:
        dist_matrix = 1 - dist_matrix
        
    if aug_diag:
        n, _ = dist_matrix.shape
        
        for i in range(n):
            dist_matrix[i,i] = np.sum(dist_matrix[i]) / (n - 1)
        
    if scale:
        if min_ is None:
            min_ = np.min(dist_matrix)
        if max_ is None:
            max_ = np.max(dist_matrix)

        dist_matrix = (dist_matrix - min_) / (max_ - min_)
                                    
    return dist_matrix