import datetime
import pandas as pd
from app.core.config import settings
import os

from app.schemas.pdesk import FinalChartData, ScatterChart

def get_scalable_model_df(label_value,model_type,lookahead_value,label_name):
    # Backtest how our model is performing on historical model
    y_range = datetime.datetime.now().year
    df_first_lookahead_list = []
    for y in range(2014, y_range):
        first_lookahead_temp_holder = pd.read_csv(os.path.join(settings.DATA_FILE_PATH,"Pdesk/static_features_temp/{}/{}/{}_lookahead_days/{}/model_output.csv".format(label_value,model_type,lookahead_value,y)))
        if len(first_lookahead_temp_holder) > 0:
            df_first_lookahead_list.append(first_lookahead_temp_holder)

    df_first_lookahead = pd.concat(df_first_lookahead_list)
    df_first_lookahead = df_first_lookahead[["Date",label_value+"actual_x_train",label_value+"_pred_with_moving_avg"]]
    df_first_lookahead["Date"] = pd.to_datetime(df_first_lookahead["Date"]).dt.date
    df_first_lookahead = df_first_lookahead.sort_values(by='Date')
    df_first_lookahead = df_first_lookahead.dropna()
    x_date = df_first_lookahead["Date"].tolist()
    y_actual = df_first_lookahead[label_value+"actual_x_train"].tolist()
    y_predicted = df_first_lookahead[label_value+"_pred_with_moving_avg"].tolist()
    graph_data = FinalChartData(data=[
        ScatterChart(x=x_date, y=y_actual, name=label_name+"-Actual"),
        ScatterChart(x=x_date, y=y_predicted, name=label_name+"-Predicted")
    ])

    return graph_data
