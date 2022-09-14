import datetime
import pandas as pd
from app.core.config import settings
import os

from app.schemas.pdesk import FinalChartData, ScatterChart, TableData


def create_graph_data(y_variable,date_value,currency,last_updated_date):
    df_final = pd.read_csv(settings.DATA_FILE_PATH+'/Pdesk/inference/' + y_variable +
                            "/USD_per_MT/30_prediction/" + date_value + "_model_prediction.csv")
    if currency == 'MYR/MT' and 'bmd' in y_variable:
        df_final[y_variable] = df_final[y_variable] * df_final['USD_MYR_Price']
    if 'bmd' not in y_variable:
        currency = '$/MT'

    x_past_date = df_final.loc[df_final['type'] == "Past"]["Date"].tolist()
    x_predicted_date = df_final.loc[df_final['type'] == "Predicted"]["Date"].tolist()
    y_past = df_final.loc[df_final['type'] == "Past"][y_variable].tolist()
    y_predicted = df_final.loc[df_final['type'] == "Predicted"][y_variable].tolist()
    return FinalChartData(data=[
                                    ScatterChart(x=x_past_date,y=y_past,name="past"),
                                    ScatterChart(x=x_predicted_date,y=y_predicted,name="predicted")
                                ],
                        last_updated_date=last_updated_date)


def create_table_data(y_variable,date_value,currency,last_updated_date):
    df_table = pd.read_csv(settings.DATA_FILE_PATH+'/Pdesk/inference/' + y_variable +
                            "/USD_per_MT/30_prediction/" + date_value + "_model_actual_predicted_data.csv")
    del df_table['Unnamed: 0']
    df_table = df_table.round(2)
    daily_prediction_data : TableData = {}
    daily_prediction_data["daily_prediction_table"] = df_table.to_dict('records')
    df_percentile = pd.read_csv(
        settings.DATA_FILE_PATH+'/Pdesk/inference/' + y_variable + "/model_percentile.csv")
    df_percentile = df_percentile.round(2)
    del df_percentile['Unnamed: 0']
    feature_percentile_data : TableData = {}
    feature_percentile_data["feature_percentile_change_table"] = df_percentile.to_dict('records')
    return TableData(data = [daily_prediction_data,feature_percentile_data], last_updated_date=last_updated_date)

def get_timedelta_date(start_date, days):
    return start_date + datetime.timedelta(days)

def get_date_range(start_date, days, is_reverse=False, reverse_end_date=None, exclude_weekdays = [5,6]):
    date_list = []
    i = 0
    count = 0
    
    while count < days:
        delta_value = -i if is_reverse else i
        dt = get_timedelta_date(start_date, delta_value)
        i = i + 1
        if reverse_end_date is not None and reverse_end_date >= dt:
            return date_list
        if dt.weekday() not in exclude_weekdays:
            count = count + 1
            date_list.append(dt.date())
    return date_list
