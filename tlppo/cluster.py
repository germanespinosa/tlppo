import typing


class Clusters(object):
    def __init__(self, data_points: typing.List[typing.Tuple[float]], cluster_count=100):
        self.data_points = data_points
        self.cluster_count = cluster_count
        from sklearn.cluster import KMeans
        self.kmeans = KMeans(n_clusters=self.cluster_count, n_init='auto', random_state=1)
        self.kmeans.fit(self.data_points)
        self.centroids = self.kmeans.cluster_centers_

    def get_labels(self, data_points: typing.List[typing.Tuple[float]]) -> typing.List[int]:
        labels = self.kmeans.predict(data_points)
        return labels


