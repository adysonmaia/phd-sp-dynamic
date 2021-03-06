import math


class KMedoids:
    """K-Metoids Clustering Algorithm

    See Also: https://www.sciencedirect.com/science/article/abs/pii/S095741740800081X

    Attributes:
        max_iterations (int): maximum number of iterations
        last_metoids (list): metoids of the last execution
    """

    def __init__(self, max_iterations=300):
        """Initialization

        Args:
            max_iterations (int): maximum number of iterations
        """
        self.max_iterations = max_iterations
        self.last_metoids = []

    def fit(self, nb_clusters, data, distances):
        """Execute clustering algorithm

        Args:
            nb_clusters (int): number of clusters
            data (list): data points
            distances (list(list)): distance between points in the data.
                It is a NxN matrix where N is the number of points in the data
        Returns:
            list(list): clustered data
        """
        r_clusters = range(nb_clusters)

        labels = {v: -1 for v in data}
        metoids = self._initial_metoids(nb_clusters, data, distances)

        clusters = None
        changed = True
        iter = 0
        while iter < self.max_iterations and changed:
            clusters = [[] for _ in r_clusters]
            changed = False
            for v in data:
                min_dist = math.inf
                new_label = -1
                for label in r_clusters:
                    metoid = metoids[label]
                    if distances[v][metoid] <= min_dist:
                        new_label = label
                        min_dist = distances[v][metoid]
                if new_label != labels[v]:
                    changed = True
                labels[v] = new_label
                clusters[new_label].append(v)

            for label in r_clusters:
                cluster = clusters[label]
                metoid = metoids[label]
                min_sum_dist = math.inf
                for v in cluster:
                    sum_dist = sum([distances[v][u] for u in cluster])
                    if sum_dist < min_sum_dist:
                        min_sum_dist = sum_dist
                        metoid = v
                metoids[label] = metoid

            iter = iter + 1
        self.last_metoids = metoids

        return clusters

    def get_last_metoids(self):
        """Get metoids (i.e., center of each cluster) found in the last execution of the algorithm

        Returns:
            list: list of metoids points
        """
        return self.last_metoids

    def _initial_metoids(self, nb_clusters, data, distances):
        """Get metoids (i.e., center of each cluster) of the first iteration

        Args:
            nb_clusters (int): number of clusters
            data (list): data points
            distances (list(list)):  distance between points in the cluster
        Returns:
            list: metoids
        """
        r_data = range(len(data))
        priority = {v: 0.0 for v in data}
        sum_dist = [sum([distances[i][l] for l in data]) for i in data]

        for j in r_data:
            for i in r_data:
                if sum_dist[i] > 0.0:
                    datum_i = data[i]
                    datum_j = data[j]
                    priority[datum_j] += distances[datum_i][datum_j] / sum_dist[i]

        s_data = sorted(data, key=lambda i: priority[i])
        metoids = s_data[:nb_clusters]
        return metoids

    def silhouette_score(self, clusters, distances):
        """Calculate Silhouette Score of the clustered data

        See Also: https://www.sciencedirect.com/science/article/pii/0377042787901257

        Args:
            clusters (list(list)): clustered data
            distances (list(list)): distance between points in the data
        Returns:
            float: score between -1 and 1
        """
        nb_clusters = len(clusters)
        r_clusters = range(nb_clusters)
        if nb_clusters <= 1:
            return 0.0
        s = sum([self._cluster_silhouette(label, clusters, distances) for label in r_clusters])
        s = s / float(len(clusters))
        return s

    def _cluster_silhouette(self, label, clusters, distances):
        """Calculate silhouette score of a specific cluster

        Args:
            label (int): index of the cluster
            clusters (list(list)): clustered data
            distances (list(list): distance between points the data
        Returns:
            float: score between -1 and 1
        """
        c = clusters[label]
        cluster_size = len(c)
        if cluster_size <= 1:
            return 0.0
        s = sum([self._datum_silhouette(datum, label, clusters, distances) for datum in c])
        s = s / float(cluster_size)
        return s

    def _datum_silhouette(self, datum, label, clusters, distances):
        """Calculate silhoutte score of a point (datum) in a specific cluster

        Args:
            datum (int): index of point in the data
            label (int): index of the cluster
            clusters (list(list)): clustered data
            distances (list(list)): distance between points in the data
        Returns:
            float: score between -1 and 1
        """
        cluster = clusters[label]
        if len(cluster) <= 1 or len(clusters) <= 1:
            return 0.0

        a = sum([distances[datum][v] for v in cluster]) / float(len(cluster))
        b = math.inf
        for c_label, c in enumerate(clusters):
            if c_label == label or len(c) == 0:
                continue
            c_b = sum([distances[datum][v] for v in c]) / float(len(c))
            if c_b < b:
                b = c_b

        if b == 0.0 and a == 0.0:
            return 0.0
        return (b - a) / float(max(b, a))
