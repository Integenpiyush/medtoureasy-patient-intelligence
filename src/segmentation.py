"""K-Means patient segmentation."""
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

def fit_personas(df, features, n_clusters=3, random_state=42):
    X = StandardScaler().fit_transform(df[features])
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=random_state)
    labels = model.fit_predict(X)
    return model, labels
