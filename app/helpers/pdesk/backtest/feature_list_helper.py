import pandas as pd
from app.core.config import settings
import os

from app.schemas.pdesk import TableData

def get_features(y_feature, month):
    if y_feature == "soyoil_cbot_prices_USD_per_MT" and month == "2":
        y_feature = "2_soyoil_cbot_prices_USD_per_MT"

    elif y_feature == "soyoil_cbot_prices_USD_per_MT" and month == "3":
        y_feature = "3_soyoil_cbot_prices_USD_per_MT"

    df = pd.read_csv(os.path.join(settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/{}/linear_regression/2_lookahead_days/{}/feature_list.csv".format(y_feature, str(month))))
    del df['Unnamed: 0']
    df = df.rename(columns={"0": "feature_name"})
    data_dict = {}
    data_dict["feature_instruments"] = df.to_dict('records')
    return TableData(data=[data_dict])
  
def get_feature_importance(y_feature, ldays):
    if y_feature == "soyoil_cbot_prices_USD_per_MT":
        y_feature = "3_soyoil_cbot_prices_USD_per_MT"
    # Here we have yused features for 2018 because its giving best result
    df = pd.read_csv(settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/{}/linear_regression/{}_lookahead_days/{}/model_output_coefficient.csv".format(y_feature, str(ldays),str(2018)))
    df = df[['feature_name', 'final_coefficient_in_per']]
    df = df.round(1)
    df = df.rename(columns={
        "feature_name": "feature_name",
        "final_coefficient_in_per": "feature_importance"
    })
    data_dict = {}
    data_dict["feature_importance"] = df.to_dict('records')
    return TableData(data=[data_dict])