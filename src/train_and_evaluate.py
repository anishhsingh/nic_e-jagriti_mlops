import os
import pandas as pd
import sys
import warnings
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import Ridge
from get_data import read_params
import argparse
import joblib
import json

def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred) 
    r2 = r2_score(actual, pred)
    return rmse, mae, r2

def train_and_evaluate(config_path):
    config = read_params(config_path)
    test_data_path = config["split_data"]["test_path"]
    train_data_path = config["split_data"]["train_path"]
    random_state = config["base"]["random_state"]
    model_dir = config["model_dir"]
    alpha = config["estimators"]["ElasticNet"]["params"]["alpha"]
    alpha_ridge = config["estimators"]["Ridge"]["params"]["alpha_ridge"]
    l1_ratio = config["estimators"]["ElasticNet"]["params"]["l1_ratio"]
    max_depth = config["estimators"]["DecisionTree"]["params"]["max_depth"]
    min_samples_split = config["estimators"]["DecisionTree"]["params"]["min_samples_split"]
    target = [config["base"]["target_col"]]

    train = pd.read_csv(train_data_path, sep=",")
    test = pd.read_csv(test_data_path, sep=",")

    train_y = train[target]
    test_y = test[target]

    train_x = train.drop(target, axis=1)
    test_x = test.drop(target, axis=1)

    train_x = train_x.select_dtypes(include=[np.number])
    test_x = test_x.select_dtypes(include=[np.number])

    lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=random_state)
    lr.fit(train_x, train_y)

    ridge = Ridge(alpha=alpha_ridge, random_state=random_state)
    ridge.fit(train_x, train_y)

    dt = DecisionTreeRegressor(max_depth=max_depth, min_samples_split=min_samples_split, random_state=random_state)
    dt.fit(train_x, train_y)

    predicted_qualities = lr.predict(test_x)

    predicted_qualities = ridge.predict(test_x)

    predicted_qualities = dt.predict(test_x)

    (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

    print("ElasticNet Model (alpha=%f, l1_ratio=%f):" % (alpha, l1_ratio))
    print("RMSE: %s" % rmse)
    print("MAE: %s" % mae)
    print("R2: %s" % r2)

    print("Ridge Model (alpha=%f):" % alpha_ridge)
    print("RMSE: %s" % rmse)
    print("MAE: %s" % mae)
    print("R2: %s" % r2)

    print("Decision Tree Model (max_depth=%f, min_samples_split=%f):" % (max_depth, min_samples_split))
    print("RMSE: %s" % rmse)
    print("MAE: %s" % mae)
    print("R2: %s" % r2)

    scores_file = config["reports"]["scores"]
    params_file = config["reports"]["params"]

    with open(scores_file, "w") as f:
        scores = {
            "rmse": rmse,
            "mae": mae,
            "r2": r2
        }
        json.dump(scores, f, indent=4)

    with open(params_file, "w") as f:
        params = {
            "alpha": alpha,
            "l1_ratio": l1_ratio,
            "alpha_ridge": alpha_ridge,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split
        }
        json.dump(params, f, indent=4)

    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")

    joblib.dump(lr, model_path)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    train_and_evaluate(config_path=parsed_args.config)
