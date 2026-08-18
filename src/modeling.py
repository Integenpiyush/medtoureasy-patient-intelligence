"""Treatment-completion modeling pipeline."""
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def build_logistic(numeric_features, categorical_features):
    num = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    cat = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                    ("ohe", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([("num", num, numeric_features), ("cat", cat, categorical_features)])
    return Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=2000, class_weight="balanced"))])

def build_random_forest(numeric_features, categorical_features):
    num = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                    ("ohe", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([("num", num, numeric_features), ("cat", cat, categorical_features)])
    model = RandomForestClassifier(
        n_estimators=500, max_depth=None, min_samples_leaf=3,
        max_features=0.7, class_weight="balanced", random_state=42, n_jobs=2
    )
    return Pipeline([("pre", pre), ("model", model)])
