import datetime
from typing import List
import pandas as pd
from app.core.config import settings
from app.schemas.pdesk import BarChart, BoxChart, FinalChartData
import numpy as np

def get_data_for_metric(y_variable, model_used, l_days, year):
    temp_df = pd.read_csv(settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/{}/{}/{}_lookahead_days/{}/model_output.csv".format(y_variable,model_used,l_days,year), index_col=[0])
    temp_df['y_unshifted'] = temp_df[y_variable + "actual_x_train"]
    temp_df['y_shifted'] = temp_df[y_variable]
    temp_df['y_prediction'] = temp_df[y_variable + '_pred_with_moving_avg']
    temp_df['y_shifted_diff'] = temp_df['y_shifted'].diff()
    temp_df['y_unshifted_diff'] = temp_df['y_unshifted'].diff()
    temp_df = temp_df[(temp_df['y_shifted_diff'] != 0) & (temp_df['y_unshifted_diff'] != 0)]
    temp_df = temp_df.reset_index()
    # y_unshifted can't be 0 , will revisit in future
    temp_df['pct_change'] = ((temp_df['y_shifted'] - temp_df['y_unshifted']) / temp_df['y_unshifted']) * 100 
    temp_df['abs_pct_change'] = temp_df['pct_change'].abs()

    actual_direction = []
    pred_direction = []
    directional_correctness = []

    for i in range(len(temp_df['y_shifted'])):
        # actual direction
        if (temp_df['y_unshifted'][i] < temp_df['y_shifted'][i]):
            actual_direction.append(1)
        else:
            actual_direction.append(0)

        # prediction direction
        if temp_df['y_unshifted'][i] < temp_df['y_prediction'][i]:
            pred_direction.append(1)
        else:
            pred_direction.append(0)
    # directional_correctness
    for i in range(len(pred_direction)):
        if ((pred_direction[i] == 0 and actual_direction[i] == 0) or 
            (pred_direction[i] == 1 and actual_direction[i] == 1)):
            directional_correctness.append(1)
        else:
            directional_correctness.append(0)
    temp_df['actual_direction'] = actual_direction
    temp_df['pred_direction'] = pred_direction
    temp_df['directional_correctness'] = directional_correctness
    temp_df.dropna(inplace=True)
    return temp_df

def metric_directional_correctness(df, val_per):
    rslt_df = df[df['abs_pct_change'] > int(val_per)]
    dir_corr = round(((len(rslt_df[rslt_df['directional_correctness']==1])/len(rslt_df))*100), 1)
    return rslt_df, dir_corr

def plotting_metric_dir_corr(y_variable, model_type, val_per):
    y_range = datetime.datetime.now().year
    l_days = [7, 15, 30]
    starting_year = 2014
    if y_variable == 'soyoil_ncdex_spot_price':
        starting_year = 2015
    data: List[BarChart] = []
    for i in l_days:
        dir_corr_lst = []
        number_of_sample = []
        year = []
        ldays = []
        for j in range(starting_year,  y_range):
            df = get_data_for_metric(y_variable, model_type, i, j)
            a, b = metric_directional_correctness(df, val_per)
            number_of_sample.append(len(a))
            dir_corr_lst.append(b)
            year.append(j)
            ldays.append(str(i))
        data.append(BarChart(x=year,y=dir_corr_lst,samples=number_of_sample,lookahead_days=ldays))
    return FinalChartData(data=data)


def metric_abs_delta_cal_plot_yearwise(y_variable, model_used="linear_regression"):
    l_days = [7, 15, 30]
    column_names = ['Date', 'y_unshifted', 'y_shifted', 'y_prediction', 'abs_delta', 'lookahead_days']
    df = pd.DataFrame(columns=column_names, dtype=object)
    if y_variable == "soyoil_ncdex_spot_price":
        for i in l_days:
            for j in range(2015, 2022):
                temp_df = pd.read_csv(settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_variable + "/" + str(model_used) + "/" + str(
                        i) + "_lookahead_days/" + str(j)+ "/model_output.csv", index_col=[0])
                # print(temp_df)
                temp_df['y_unshifted'] = temp_df[y_variable + "actual_x_train"]
                temp_df['y_shifted'] = temp_df[y_variable]
                temp_df['y_prediction'] = temp_df[y_variable + '_pred_with_moving_avg']
                temp_df['lookahead_days'] = i
                df = pd.concat([df, temp_df], axis=0)
        
        df['abs_delta'] = ((abs(df['y_prediction'] - df['y_shifted']) / df['y_shifted']) * 100).round(1)
        df['year'] = pd.DatetimeIndex(df['Date']).year
        return df

    elif y_variable == 'basis_spot_future_bmd' or y_variable== 'basis_spot_future_mcx'\
            or y_variable == 'basis_spot(argentina)_future(3SoyoilCbot)' or y_variable =='basis_spot(argentina)_future(2SoyoilCbot)':
        for i in l_days:
            for j in range(2014, 2022):
                temp_df = pd.read_csv(
                    settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_variable + "/" + str(model_used) + "/" + str(
                        i) + "_lookahead_days/" + str(j) + "/model_output.csv", index_col=[0])

                temp_df['y_unshifted'] = temp_df[y_variable + "actual_x_train"]
                temp_df['y_shifted'] = temp_df[y_variable]
                temp_df['y_prediction'] = temp_df[y_variable + '_pred_with_moving_avg']
                temp_df['lookahead_days'] = i
                df = pd.concat([df, temp_df], axis=0)

        df = df[df["y_shifted"]!=0]
        df['abs_delta'] = ((abs((df['y_prediction'] - df['y_shifted']) / df['y_shifted'])) * 100).astype("float").round(1)
        df['year'] = pd.DatetimeIndex(df['Date']).year

        if y_variable == 'basis_spot_future_bmd' or y_variable== 'basis_spot_future_mcx':
            for year in range(2014, 2023):
                value = abs((df["abs_delta"].median()))
                df["abs_delta"] = np.where(((df["abs_delta"] >= value * 25)) & (df['year'] == year),
                                           df["abs_delta"].median(), df["abs_delta"])

            return df
        elif y_variable == 'basis_spot(argentina)_future(3SoyoilCbot)' or y_variable =='basis_spot(argentina)_future(2SoyoilCbot)':
            for year in range(2014, 2023):
                value = abs((df["abs_delta"].median()))
                df["abs_delta"] = np.where(((df["abs_delta"] >= value * 15)) & (df['year'] == year),
                                           df["abs_delta"].median(), df["abs_delta"])

            return df

    else:

        for i in l_days:
            for j in range(2014, 2022):
                temp_df = pd.read_csv(settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_variable + "/" + str(model_used) + "/" + str(
                        i) + "_lookahead_days/" + str(j)+ "/model_output.csv", index_col=[0])
                # print(temp_df)
                temp_df['y_unshifted'] = temp_df[y_variable + "actual_x_train"]
                temp_df['y_shifted'] = temp_df[y_variable]
                temp_df['y_prediction'] = temp_df[y_variable + '_pred_with_moving_avg']
                temp_df['lookahead_days'] = i
                df = pd.concat([df, temp_df], axis=0)

            # print(df)
    df['abs_delta'] = ((abs(df['y_prediction'] - df['y_shifted']) / df['y_shifted']) * 100).astype(float).round(1)
    df['year'] = pd.DatetimeIndex(df['Date']).year
    # print(df['abs_delta'])

    return df[['abs_delta','year','lookahead_days']]

def box_plot_data(y_variable,model_type):
    df = metric_abs_delta_cal_plot_yearwise(y_variable,model_type)
    # Removing nan values as json doesn't acces nan
    df = df[df['abs_delta'].notna()]
    gb_df = df.groupby(df["lookahead_days"])
    graph_data = []
    for lookahead in df["lookahead_days"].unique():
        x_data = gb_df.get_group(lookahead)["year"].astype(str).tolist()
        y_data = gb_df.get_group(lookahead)["abs_delta"].tolist()
        graph_data.append(BoxChart(x=x_data,y=y_data,name=str(lookahead)))
    final_graph_data = FinalChartData(data=graph_data)
    # df.to_csv("delta.csv")
    return final_graph_data
