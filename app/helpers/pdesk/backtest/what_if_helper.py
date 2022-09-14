import os
import warnings
from app.core.cache import get_cache, set_cache

from app.schemas.pdesk import FinalChartData, ScatterChart
from app.util.query import get_data_from_query, get_table_columns, get_table_data
warnings.filterwarnings("ignore")
import pandas as pd
pd.set_option('mode.use_inf_as_na', True)
import numpy as np
import base64
import boto3
from pandas.tseries.offsets import MonthEnd, MonthBegin
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import pickle
from datetime import datetime
import math
from datetime import datetime
from datetime import timedelta, date
import talib
from app.core.config import settings
from pandas.tseries.offsets import Week
from app.util import common


date_column = "Date"
is_3_month_active = 0
pdesk_what_if_redis_prefix = "pdesk_what_if" 
lookahead_days = 8

def merge_daily_monthly_data():
    df_final_pdesk = get_cache("pdesk_what_if_final_df")
    df_final_pdesk_2soyoil_arg = get_cache("pdesk_what_if_2_soyoil_df")
    df_final_pdesk_3soyoil_arg = get_cache("pdesk_what_if_3_soyoil_df")
    df_final_pdesk_daily=get_cache("pdesk_what_if_daily_final_df")
    if(isinstance(df_final_pdesk, pd.DataFrame) and len(df_final_pdesk)>0 and
        isinstance(df_final_pdesk_2soyoil_arg, pd.DataFrame) and len(df_final_pdesk_2soyoil_arg)>0 and 
        isinstance(df_final_pdesk_3soyoil_arg, pd.DataFrame) and len(df_final_pdesk_3soyoil_arg)>0 and
        isinstance(df_final_pdesk_daily, pd.DataFrame) and len(df_final_pdesk_daily)>0):
        return df_final_pdesk, df_final_pdesk_2soyoil_arg, df_final_pdesk_3soyoil_arg, df_final_pdesk_daily
    else:
        # Daily data
        df_daily_columns = get_table_columns("pdesk_edibleoil_daily_features")
        df_daily = pd.DataFrame(get_table_data("pdesk_edibleoil_daily_features"), columns=df_daily_columns)
        del df_daily['index']
        df_daily['Date'] = pd.to_datetime(df_daily['Date'])
        df_daily = df_daily.sort_values(by="Date")

        # this mapping is required to replace the NSLR values to zero
        mapping = {'NSLR': 0}
        df_daily = df_daily.replace({'third_month_argentina_spot_price': mapping, 'four_month_argentina_spot_price': mapping})
        for columns in df_daily.columns:
            if columns != 'Date':  # we dont want to change the datatype for Date column
                df_daily[columns] = df_daily[columns].apply(pd.to_numeric)

        # weather index addign in dataframe
        df_cpo_index_columns = get_table_columns("palm_oil_index")
        df_palm_oil_index = pd.DataFrame(get_table_data("weather_data.palm_oil_index"), columns=df_cpo_index_columns)
        del df_palm_oil_index['index']
        df_palm_oil_index['Date'] = pd.to_datetime(df_palm_oil_index['Date'])

        # merging daily df with palm oil index d
        df_daily = pd.merge(df_daily, df_palm_oil_index, left_on="Date", right_on="Date", how="left")

        # Month Data
        df_monthly_columns = get_table_columns("pdesk_edibleoil_monthwise_features")
        df_monthly = pd.DataFrame(get_table_data("pdesk_edibleoil_monthwise_features"), columns=df_monthly_columns)
        del df_monthly['index']
        df_monthly = df_monthly.sort_values(by=["Year", "Month"])
        for columns in df_monthly.columns:
            if columns != 'Date':  # we dont want to change the datatype for Date column
                df_monthly[columns] = df_monthly[columns].apply(pd.to_numeric)

        df_monthly.drop_duplicates(inplace = True)
        df_monthly['month_date'] = df_monthly["Month"].astype(int).astype(str) + "/" +df_monthly["Year"].astype(int).astype(str)

        df_monthly['legged_start_month_date'] = pd.to_datetime(df_monthly["Month"].astype(int).astype(str) + "/" +df_monthly["Year"].astype(int).astype(str) + "/1", format="%m/%Y/%d")

        tolerance_day = pd.Timedelta('30 day')
        df_final_pdesk = pd.merge_asof(left=df_daily.sort_values('Date'),right=df_monthly.sort_values('legged_start_month_date'), left_on="Date", right_on="legged_start_month_date", direction='backward',tolerance=tolerance_day)
        df_final_pdesk = df_final_pdesk.sort_values(by="Date") # sorting final dataframe on date column
        df_final_pdesk['basis_spot_future_bmd'] = df_final_pdesk['bmd_spot_price'] - df_final_pdesk['3_cpo_bmd_prices_USD_per_MT']
        df_final_pdesk['basis_spot_future_mcx'] = df_final_pdesk['mcx_spot_price'] - df_final_pdesk['3_cpo_bmd_prices_USD_per_MT']

        # creating new column Argentina_Soyoil
        df_final_pdesk['Argentina_Soyoil'] = np.select([df_final_pdesk['first_month_argentina_spot_price'] != 0 , df_final_pdesk['second_month_argentina_spot_price'] != 0, df_final_pdesk['third_month_argentina_spot_price'] != 0], [df_final_pdesk['first_month_argentina_spot_price'], df_final_pdesk['second_month_argentina_spot_price'], df_final_pdesk['third_month_argentina_spot_price'], ], default=df_final_pdesk['four_month_argentina_spot_price'])
        df_final_pdesk['Argentina_Soyoil_minus_Malaysia_CPO_Spot'] = df_final_pdesk["Argentina_Soyoil"] - df_final_pdesk["bmd_spot_price"]

        global is_3_month_active
        is_3_month_active = math.isnan(df_final_pdesk.iloc[-1, :]["2_soyoil_cbot_prices_USD_per_MT"])

        # copying data befor ffill bfill for calculating 75th percentile
        # df_final_pdesk_clculate_75th_percentile = df_final_pdesk.copy() # copying original data to calculate 75th percentile

        # not apply ffill and bfill to basis argentina
        df_3_soyoil_cbot = df_final_pdesk['3_soyoil_cbot_prices_USD_per_MT']
        df_2_soyoil_cbot = df_final_pdesk['2_soyoil_cbot_prices_USD_per_MT']
                
        df_final_pdesk = df_final_pdesk.fillna(method='ffill')
        df_final_pdesk = df_final_pdesk.fillna(method='bfill')
        #below dataframe will be used for basis argentina minus 2_soyoil_cbot_prices_USD_per_MT
        df_final_pdesk_2soyoil_arg = df_final_pdesk.copy()
        df_final_pdesk_2soyoil_arg['2_soyoil_cbot_prices_USD_per_MT'] = df_2_soyoil_cbot
        df_final_pdesk_2soyoil_arg['basis_spot(argentina)_future(2SoyoilCbot)'] = df_final_pdesk_2soyoil_arg['Argentina_Soyoil'] - df_final_pdesk_2soyoil_arg['2_soyoil_cbot_prices_USD_per_MT']
        df_final_pdesk_2soyoil_arg = df_final_pdesk_2soyoil_arg[df_final_pdesk_2soyoil_arg['2_soyoil_cbot_prices_USD_per_MT'].notna()]

        # below dataframe will be used for basis argentina minus 3_soyoil_cbot_prices_USD_per_MT
        df_final_pdesk_3soyoil_arg = df_final_pdesk.copy()
        df_final_pdesk_3soyoil_arg['3_soyoil_cbot_prices_USD_per_MT'] = df_3_soyoil_cbot
        df_final_pdesk_3soyoil_arg['basis_spot(argentina)_future(3SoyoilCbot)'] = df_final_pdesk_3soyoil_arg['Argentina_Soyoil'] - df_final_pdesk_3soyoil_arg['3_soyoil_cbot_prices_USD_per_MT']
        df_final_pdesk_3soyoil_arg = df_final_pdesk_3soyoil_arg[df_final_pdesk_3soyoil_arg['3_soyoil_cbot_prices_USD_per_MT'].notna()]
        
        df_final_pdesk['indonesia_nobis_palmoil_stock'] = df_final_pdesk['indonesia_palmoil_production_in_MT'] - df_final_pdesk['indonesia_cpo_domestic_consumption_in_MT'] - df_final_pdesk['cpo_export_allpalmoil_indonesia_in_MT'] + 2000000
        df_final_pdesk_daily = df_final_pdesk.copy()
        df_final_pdesk = df_final_pdesk.sort_values(by="Date") # sorting final dataframe on date column

        df_final_pdesk['Date'] = df_final_pdesk['Date'] + Week(weekday=4)
        df_final_pdesk = df_final_pdesk.groupby(['Date']).mean()
        df_final_pdesk = df_final_pdesk.reset_index()

        df_final_pdesk_2soyoil_arg['Date'] = df_final_pdesk_2soyoil_arg['Date'] + Week(weekday=4)
        df_final_pdesk_2soyoil_arg = df_final_pdesk_2soyoil_arg.groupby(['Date']).mean()
        df_final_pdesk_2soyoil_arg = df_final_pdesk_2soyoil_arg.reset_index()

        df_final_pdesk_3soyoil_arg['Date'] = df_final_pdesk_3soyoil_arg['Date'] + Week(weekday=4)
        df_final_pdesk_3soyoil_arg = df_final_pdesk_3soyoil_arg.groupby(['Date']).mean()
        df_final_pdesk_3soyoil_arg = df_final_pdesk_3soyoil_arg.reset_index()
        set_cache("pdesk_what_if_final_df",df_final_pdesk, expiry_time=settings.time_to_expire)
        set_cache("pdesk_what_if_2_soyoil_df",df_final_pdesk_2soyoil_arg, expiry_time=settings.time_to_expire)
        set_cache("pdesk_what_if_3_soyoil_df",df_final_pdesk_2soyoil_arg, expiry_time=settings.time_to_expire)
        set_cache("pdesk_what_if_daily_final_df",df_final_pdesk_daily, expiry_time=settings.time_to_expire)
        return df_final_pdesk, df_final_pdesk_2soyoil_arg, df_final_pdesk_3soyoil_arg,df_final_pdesk_daily

def base_what_if(y_column):
    ''' This fuction is to get the base what if prediction
    We can cache this'''
    date_key = common.today_date_key()
   
    df_final_base = get_cache(f"pdesk_what_if_final_base_df_{date_key}_{y_column}")
    if(isinstance(df_final_base,pd.DataFrame) and len(df_final_base)>0):
        return df_final_base
    else: 
        df_final_pdesk, df_final_pdesk_2soyoil_arg, df_final_pdesk_3soyoil_arg, _ = merge_daily_monthly_data()
        start_year = 2014
        usd_myr_column = "USD_MYR_Price"

        if y_column == "basis_spot(argentina)_future(3SoyoilCbot)":
            temp = df_final_pdesk_3soyoil_arg[df_final_pdesk_3soyoil_arg["Year"] >= start_year]

        elif y_column == "basis_spot(argentina)_future(2SoyoilCbot)":
            temp = df_final_pdesk_2soyoil_arg[df_final_pdesk_2soyoil_arg["Year"] >= start_year]

        else:
            temp = df_final_pdesk[df_final_pdesk['Year'] >= start_year]
        all_y_column = temp[[y_column]]
        all_lookahead_percentile = []
        
        # for th base gam model predictions (here no input is being taken from the user)
        # this will store all the prediction for the n day
        predictions = []
        lr_raw_prediction = []
        usd_myr_price_list = []

        for day in range(1, lookahead_days + 1):
            x_column = get_feature_list_from_s3(y_column, day, is_3_month_active)

            # get prediction for the n days
            df_actual, prediction, lr_prediction, percentile_change = get_prediction(temp, x_column, y_column, day, all_y_column, is_3_month_active)


            # storeing the prediction
            predictions.append(prediction[0])

            # storing the raw prediction
    #         print(lr_prediction)
            lr_raw_prediction.append(lr_prediction)

            # storing the usd_myr_price
            usd_myr_price_list.append(df_actual[usd_myr_column].tail(1).values[0])

            # appending the dictionary lookahead and percentile change
            all_lookahead_percentile.append({ "Lookahead": str(day) + "_Lookahead", "percentile": percentile_change })


        df_final_base, df_actual_prediction_base = merge_prediction_dataframe(temp, y_column, usd_myr_column, day, predictions, usd_myr_price_list, lr_raw_prediction)
        df_final_base = df_final_base.sort_values('Date')
        df_final_base["moving_avg"] = df_final_base[y_column].rolling(7).mean()
        df_actual_prediction_base["moving_avg"] = df_final_base["moving_avg"].tail(day).values


        # we changing the predicted value with the moving average
        df_final_base[y_column] = np.where(df_final_base["type"] == "Predicted", df_final_base["moving_avg"], df_final_base[y_column])


        # sorting the value based on the date
        df_final_base = df_final_base.sort_values('Date')

        df_final_base = df_final_base.tail(150)
        set_cache(f"pdesk_what_if_final_base_df_{date_key}_{y_column}", df_final_base, expiry_time=settings.time_to_expire)
        return df_final_base

def create_technical_features(df):#, lookahead, y_variable, temperature_index, precip_index, volume_feature):
    
    # '''
    # I/P - df, lookahead, y_variable
    
    # creating 4 types of technical features
    
    # O/P - dataframe with 4 types of technical features'''
    
    # df1 = df.copy()
    
    # if volume_feature == "third_month_future_volume_bmd_in_MT":
    #     # Simple moving average
    #     df1['SMA_'+str(lookahead)+'_'+y_variable]=df1.loc[:,y_variable].rolling(window=lookahead).mean()
    #     df1['SMA_'+str(lookahead)+'_'+temperature_index]=df1.loc[:,temperature_index].rolling(window=lookahead).mean()
    #     df1['SMA_'+str(lookahead)+'_'+precip_index]=df1.loc[:,precip_index].rolling(window=lookahead).mean()
    #     df1['SMA_'+str(lookahead)+'_'+volume_feature]=df1.loc[:,volume_feature].rolling(window=lookahead).mean()

    #     #exponential moving average
    #     df1['EMA_'+str(lookahead)+'_'+y_variable]=df1.loc[:,y_variable].ewm(span=lookahead).mean()
    #     df1['EMA_'+str(lookahead)+'_'+temperature_index]=df1.loc[:,temperature_index].ewm(span=lookahead).mean()
    #     df1['EMA_'+str(lookahead)+'_'+precip_index]=df1.loc[:,precip_index].ewm(span=lookahead).mean()
    #     df1['EMA_'+str(lookahead)+'_'+volume_feature]=df1.loc[:,volume_feature].ewm(span=lookahead).mean()

    #     # Rate of Change 
    #     df1['ROC_'+str(lookahead)+'_'+y_variable]=(df1[y_variable]-df1[y_variable].shift(lookahead))/df1[y_variable].shift(lookahead) * 100
    #     df1['ROC_'+str(lookahead)+'_'+temperature_index]=(df1[temperature_index]-df1[temperature_index].shift(lookahead))/df1[temperature_index].shift(lookahead) * 100
    #     df1['ROC_'+str(lookahead)+'_'+precip_index]=(df1[precip_index]-df1[precip_index].shift(lookahead))/df1[precip_index].shift(lookahead) * 100
    #     df1['ROC_'+str(lookahead)+'_'+volume_feature]=(df1[volume_feature]-df1[volume_feature].shift(lookahead))/df1[volume_feature].shift(lookahead) * 100

    #     flag_check_RSI = False
    #     if lookahead > 1:
    #         # Relative strength index
    #         df1['RSI_'+str(lookahead)+'_'+y_variable]=talib.RSI(df1[y_variable],timeperiod=lookahead)
    #         df1['RSI_'+str(lookahead)+'_'+temperature_index]=talib.RSI(df1[temperature_index],timeperiod=lookahead)
    #         df1['RSI_'+str(lookahead)+'_'+precip_index]=talib.RSI(df1[precip_index],timeperiod=lookahead)
    #         df1['RSI_'+str(lookahead)+'_'+volume_feature]=talib.RSI(df1[volume_feature],timeperiod=lookahead)
    #         flag_check_RSI = True

    #     if flag_check_RSI:
    #         df_temp_y_variable = df1[['SMA_'+str(lookahead)+'_'+y_variable, 'EMA_'+str(lookahead)+'_'+y_variable, 'ROC_'+str(lookahead)+'_'+y_variable, 'RSI_'+str(lookahead)+'_'+y_variable]]
    #         df_temp_y_variable_temperature = df1[['SMA_'+str(lookahead)+'_'+temperature_index, 'EMA_'+str(lookahead)+'_'+temperature_index, 'ROC_'+str(lookahead)+'_'+temperature_index, 'RSI_'+str(lookahead)+'_'+temperature_index]]
    #         df_temp_y_variable_precip = df1[['SMA_'+str(lookahead)+'_'+precip_index, 'EMA_'+str(lookahead)+'_'+precip_index, 'ROC_'+str(lookahead)+'_'+precip_index, 'RSI_'+str(lookahead)+'_'+precip_index]]
    #         df_temp_y_variable_volume_feature = df1[['SMA_'+str(lookahead)+'_'+volume_feature, 'EMA_'+str(lookahead)+'_'+volume_feature, 'ROC_'+str(lookahead)+'_'+volume_feature, 'RSI_'+str(lookahead)+'_'+volume_feature]]
    #     else:
    #         df_temp_y_variable = df1[['SMA_'+str(lookahead)+'_'+y_variable, 'EMA_'+str(lookahead)+'_'+y_variable, 'ROC_'+str(lookahead)+'_'+y_variable]]
    #         df_temp_y_variable_temperature = df1[['SMA_'+str(lookahead)+'_'+temperature_index, 'EMA_'+str(lookahead)+'_'+temperature_index, 'ROC_'+str(lookahead)+'_'+temperature_index]]
    #         df_temp_y_variable_precip = df1[['SMA_'+str(lookahead)+'_'+precip_index, 'EMA_'+str(lookahead)+'_'+precip_index, 'ROC_'+str(lookahead)+'_'+precip_index]]
    #         df_temp_y_variable_volume_feature = df1[['SMA_'+str(lookahead)+'_'+volume_feature, 'EMA_'+str(lookahead)+'_'+volume_feature, 'ROC_'+str(lookahead)+'_'+volume_feature]]

    #     df1.replace([np.inf, -np.inf], np.nan, inplace=True)
    #     df1=df1.fillna(df_temp_y_variable.mean(skipna=True))
    #     df1=df1.fillna(df_temp_y_variable_temperature.mean(skipna=True))
    #     df1=df1.fillna(df_temp_y_variable_precip.mean(skipna=True))
    #     df1=df1.fillna(df_temp_y_variable_volume_feature.mean(skipna=True))

    #     return df1

    # else:
    #     # Simple moving average
    #     df1['SMA_'+str(lookahead)+'_'+y_variable]=df1.loc[:,y_variable].rolling(window=lookahead).mean()
    #     df1['SMA_'+str(lookahead)+'_'+volume_feature]=df1.loc[:,volume_feature].rolling(window=lookahead).mean()

    #     #exponential moving average
    #     df1['EMA_'+str(lookahead)+'_'+y_variable]=df1.loc[:,y_variable].ewm(span=lookahead).mean()
    #     df1['EMA_'+str(lookahead)+'_'+volume_feature]=df1.loc[:,volume_feature].ewm(span=lookahead).mean()

    #     # Rate of Change 
    #     df1['ROC_'+str(lookahead)+'_'+y_variable]=(df1[y_variable]-df1[y_variable].shift(lookahead))/df1[y_variable].shift(lookahead) * 100
    #     df1['ROC_'+str(lookahead)+'_'+volume_feature]=(df1[volume_feature]-df1[volume_feature].shift(lookahead))/df1[volume_feature].shift(lookahead) * 100

    #     flag_check_RSI = False
    #     if lookahead > 1:
    #         # Relative strength index
    #         df1['RSI_'+str(lookahead)+'_'+y_variable]=talib.RSI(df1[y_variable],timeperiod=lookahead)
    #         df1['RSI_'+str(lookahead)+'_'+volume_feature]=talib.RSI(df1[volume_feature],timeperiod=lookahead)
    #         flag_check_RSI = True

    #     if flag_check_RSI:
    #         df_temp_y_variable = df1[['SMA_'+str(lookahead)+'_'+y_variable, 'EMA_'+str(lookahead)+'_'+y_variable, 'ROC_'+str(lookahead)+'_'+y_variable, 'RSI_'+str(lookahead)+'_'+y_variable]]
    #         df_temp_y_variable_volume_feature = df1[['SMA_'+str(lookahead)+'_'+volume_feature, 'EMA_'+str(lookahead)+'_'+volume_feature, 'ROC_'+str(lookahead)+'_'+volume_feature, 'RSI_'+str(lookahead)+'_'+volume_feature]]
    #     else:
    #         df_temp_y_variable = df1[['SMA_'+str(lookahead)+'_'+y_variable, 'EMA_'+str(lookahead)+'_'+y_variable, 'ROC_'+str(lookahead)+'_'+y_variable]]
    #         df_temp_y_variable_volume_feature = df1[['SMA_'+str(lookahead)+'_'+volume_feature, 'EMA_'+str(lookahead)+'_'+volume_feature, 'ROC_'+str(lookahead)+'_'+volume_feature]]

    #     df1.replace([np.inf, -np.inf], np.nan, inplace=True)
    #     df1=df1.fillna(df_temp_y_variable.mean(skipna=True))
    #     df1=df1.fillna(df_temp_y_variable_volume_feature.mean(skipna=True))

        return df

def get_prediction_of_lrgam(df, y_column, day, is_3_month_active):
    month_folder = 3 if is_3_month_active else 2 
    dir_path = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/"+ str(month_folder)
    file = "/production_what_if_"+ y_column + ".pkl"
    linear_regression_model = None
    with open(dir_path+file,"rb") as fp:
        linear_regression_model = pickle.load(fp)
    return linear_regression_model.predict(df)

def get_prediction_of_lrgam_daily(df, y_column, day, is_3_month_active):
    
    month_folder = 3 if is_3_month_active else 2 
    dir_path = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/"+ str(month_folder)
    file = "/production_what_if_"+ y_column + ".pkl"
    linear_regression_model = None
    with open(dir_path+file,"rb") as fp:
        linear_regression_model = pickle.load(fp)
    return linear_regression_model.predict(df)

def get_scaler(y_column, day, is_3_month_active):
    month_folder = 3 if is_3_month_active else 2 
    file_path_scaler_x = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/" + str(month_folder)
    file_name_scaler_x = "/scaler_x_what_if_"+ y_column + ".pkl"
    scaler_x = None
    with open(file_path_scaler_x+file_name_scaler_x,"rb") as fp:
        scaler_x = pickle.load(fp)
    
    file_path_scaler_y = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/" + str(month_folder)
    file_name_scaler_y = "/scaler_y_what_if_"+ y_column + ".pkl"
    scaler_y = None
    with open(file_path_scaler_y+file_name_scaler_y,"rb") as fp:
        scaler_y = pickle.load(fp)
    
    return scaler_x, scaler_y

def get_scaler_daily(y_column, day, is_3_month_active):
    month_folder = 3 if is_3_month_active else 2 
    file_path_scaler_x = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/" + str(month_folder)
    file_name_scaler_x = "/scaler_x_what_if_"+ y_column + ".pkl"
    scaler_x = None
    with open(file_path_scaler_x+file_name_scaler_x,"rb") as fp:
        scaler_x = pickle.load(fp)
    
    file_path_scaler_y = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/" + str(month_folder)
    file_name_scaler_y = "/scaler_y_what_if_"+ y_column + ".pkl"
    scaler_y = None
    with open(file_path_scaler_y+file_name_scaler_y,"rb") as fp:
        scaler_y = pickle.load(fp)
    
    return scaler_x, scaler_y

def get_feature_list_from_s3(y_column, day, is_3_month_active):
    month_folder = 3 if is_3_month_active else 2 
    dir_path = settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_column + "/linear_gam_weekly/" + str(day) + "_lookahead_days/" + str(month_folder)
    file = "/feature_list_what_if_"+ y_column + ".csv"
    df = pd.read_csv(dir_path+file, index_col=[0])
    return df.iloc[:,0].values


def get_scaler_df(x_test, y_test, y_column, day, is_3_month_active):
    scaler_x, scaler_y = get_scaler(y_column, day, is_3_month_active)

    x_test_scaled = scaler_x.transform(x_test.copy().astype(float))
    x_test_df_scaled = pd.DataFrame(x_test_scaled)
    x_test_df_scaled.columns = x_test.columns
    x_test = x_test_df_scaled
    
    y_test_scaled = scaler_y.transform(y_test.astype(float))
    y_test_df_scaled = pd.DataFrame(y_test_scaled)
    y_test_df_scaled.columns=y_test.columns
    y_test = y_test_df_scaled

    return x_test, y_test, scaler_y

def get_scaler_df_daily(x_test, y_test, y_column, day, is_3_month_active):
    scaler_x, scaler_y = get_scaler_daily(y_column, day, is_3_month_active)

    x_test_scaled = scaler_x.transform(x_test.copy().astype(float))
    x_test_df_scaled = pd.DataFrame(x_test_scaled)
    x_test_df_scaled.columns = x_test.columns
    x_test = x_test_df_scaled
    
    y_test_scaled = scaler_y.transform(y_test.astype(float))
    y_test_df_scaled = pd.DataFrame(y_test_scaled)
    y_test_df_scaled.columns=y_test.columns
    y_test = y_test_df_scaled

    return x_test, y_test, scaler_y

def apply_unscaling(y_pred, scaler_y):
    # Need to discuss
    y_pred = scaler_y.inverse_transform(y_pred.reshape(-1,1))    
    return y_pred

def get_prediction(df, x_columns, y_column, day, all_y_column, is_3_month_active): 
    
    df = df.sort_values(by=["Date"]) # sorting the dataframe based on date
    
    # created copy because remove method remove the 
    x_columns_copy = x_columns.copy()
    
    if "SMA_" + str(day) + "_third_month_future_volume_soyoil_cbot_in_MT" in x_columns_copy:
        volume_feature = "third_month_future_volume_soyoil_cbot_in_MT"

    elif "SMA_" + str(day) + "_third_month_future_volume_bmd_in_MT" in x_columns_copy:
        volume_feature = "third_month_future_volume_bmd_in_MT"
        
    # getting technical feature
    df_features = create_technical_features(df) #, day, y_column, 'temperature_index', 'precipitation_index', volume_feature)

    # making x column copy
    x_col = x_columns.copy()

    # making dataframe copy
    df_rf = df_features.copy()

    # adding the actual value for training
    df_rf[y_column + "_actual_for_training"] = df_rf[y_column].copy()

    # filttering the x_col data
    x_test = df_rf[x_col]

    # remove the y_column from the test
    y_test = x_test[[y_column]]
    del x_test[y_column]
    del x_test['Date']

    # converting into scaled values
    x_test_scaler, y_test_scaler, scaler_y = get_scaler_df(x_test, y_test,y_column,day,is_3_month_active)
    x_test_scaler = x_test_scaler.tail(1).copy()
    y_test_scaler = y_test_scaler.tail(1).copy()

    # predicting the new data using Linear regression
    lr_prediction_scaled = get_prediction_of_lrgam(x_test_scaler, y_column, day, is_3_month_active)
    lr_prediction_unscaled = apply_unscaling(lr_prediction_scaled, scaler_y)
    
    x_test = x_test.tail(1).copy()
    # assning the value to column predition
    x_test[y_column + "_prediction"] = lr_prediction_unscaled
    
    # getting the new percentile prediction
    if y_column =='basis_spot(argentina)_future(3SoyoilCbot)' or y_column =='basis_spot(argentina)_future(2SoyoilCbot)':
        percentile_prediction, percentile_change = get_95_percentile_prediction(all_y_column, x_test, day, y_column)
    else:
        percentile_prediction, percentile_change = get_75_percentile_prediction(all_y_column, x_test, day, y_column)

    return df_features, percentile_prediction, lr_prediction_unscaled, percentile_change

def get_prediction_daily(df, x_columns, y_column, day, all_y_column, is_3_month_active): 
    
    df = df.sort_values('Date') # sorting the dataframe based on date
    
    # created copy because remove method remove the 
    x_columns_copy = x_columns.copy()
    
    if "SMA_" + str(day) + "_third_month_future_volume_soyoil_cbot_in_MT" in x_columns_copy:
        volume_feature = "third_month_future_volume_soyoil_cbot_in_MT"

    elif "SMA_" + str(day) + "_third_month_future_volume_bmd_in_MT" in x_columns_copy:
        volume_feature = "third_month_future_volume_bmd_in_MT"
        
    # getting technical feature
    df_features = create_technical_features(df) #, day, y_column, 'temperature_index', 'precipitation_index', volume_feature)
    
    # making x column copy
    x_col = x_columns.copy()

    # making dataframe copy
    df_rf = df_features.copy()

    # adding the actual value for training
    df_rf[y_column + "_actual_for_training"] = df_rf[y_column].copy()

    # adding technical feature column to the x col
#     x_col = get_feauture_list(df_rf, x_col, y_column)

    # filttering the x_col data
    x_test = df_rf[x_col]

    # remove the y_column from the test
    y_test = x_test[[y_column]]
    del x_test[y_column]
    del x_test['Date']

    # converting into scaled values
    x_test_scaler, y_test_scaler, scaler_y = get_scaler_df_daily(x_test, y_test,y_column,day,is_3_month_active)
    
#     print('x test', x_test)
    x_test_scaler = x_test_scaler.tail(1).copy()
    y_test_scaler = y_test_scaler.tail(1).copy()

    # predicting the new data using Linear regression
    lr_prediction_scaled = get_prediction_of_lrgam_daily(x_test_scaler, y_column, day, is_3_month_active)
    lr_prediction_unscaled = apply_unscaling(lr_prediction_scaled, scaler_y)
    
#     print(x_test, lr_prediction)
    
    x_test = x_test.tail(1).copy()
    # assning the value to column predition
    x_test[y_column + "_prediction"] = lr_prediction_unscaled
    
    
    
    # getting the new percentile prediction
    if y_column =='basis_spot(argentina)_future(3SoyoilCbot)' or y_column =='basis_spot(argentina)_future(2SoyoilCbot)':
        percentile_prediction, percentile_change = get_95_percentile_prediction(all_y_column, x_test, day, y_column)
    else:
        percentile_prediction, percentile_change = get_75_percentile_prediction(all_y_column, x_test, day, y_column)

    return df_features, percentile_prediction, lr_prediction_unscaled, percentile_change

def get_75_percentile_prediction(all_y_column, df_final_pred,  l_days, y_variable):
    final_percentile_change = np.percentile(np.array(all_y_column[y_variable].dropna().pct_change(l_days).dropna()*100), 75)
    final_prediction = []
    
    for act_val, predicted_val in zip(df_final_pred[y_variable + "_actual_for_training"], df_final_pred[y_variable + "_prediction"]):
        limit1 = ((act_val + (final_percentile_change * act_val) / 100))
        limit2 = ((act_val - (final_percentile_change * act_val) / 100))
        if limit1 > limit2:
            upper_limit = limit1
            lower_limit = limit2
        else:
            upper_limit = limit2
            lower_limit = limit1
            
        if (predicted_val > upper_limit):
            final_prediction.append(predicted_val)

        elif (predicted_val < lower_limit):
            final_prediction.append(predicted_val)

        else:
            final_prediction.append(predicted_val)
       

    return final_prediction, final_percentile_change

def get_95_percentile_prediction(all_y_column, df_final_pred,  l_days, y_variable):
    final_percentile_change = np.percentile(np.array(all_y_column[y_variable].dropna().pct_change(l_days).dropna()*100), 95)
    final_prediction = []
    
    for act_val, predicted_val in zip(df_final_pred[y_variable + "_actual_for_training"], df_final_pred[y_variable + "_prediction"]):
        limit1 = ((act_val + (final_percentile_change * act_val) / 100))
        limit2 = ((act_val - (final_percentile_change * act_val) / 100))
        if limit1 > limit2:
            upper_limit = limit1
            lower_limit = limit2
        else:
            upper_limit = limit2
            lower_limit = limit1
            
        if (predicted_val > upper_limit):
            final_prediction.append(upper_limit)

        elif (predicted_val < lower_limit):
            final_prediction.append(lower_limit)

        else:
            final_prediction.append(predicted_val)

    return final_prediction, final_percentile_change

def get_timedelta_date(start_date, days):
    return start_date + timedelta(days)

def get_date_range(start_date, days):
    date_list = []
    weekdays = [5,6]
    i = 0
    count = 0
    while count < days:
        dt = get_timedelta_date(start_date, i)
        i = i + 1
        if dt.weekday() not in weekdays:
            count = count + 1
            date_list.append(dt.date())
    test_pd  = pd.DataFrame({'Date':date_list})
    test_pd['Date'] = pd.to_datetime(test_pd['Date']).dt.date
    test_pd['Date'] = test_pd['Date'] + Week(weekday=4)
    test_pd['Date'] = pd.to_datetime(test_pd['Date']).dt.date
    return test_pd['Date'].unique()[:8]

def merge_prediction_dataframe(df, y_column, usd_myr_column, day, predictions, usd_myr_price_list, lr_raw_prediction):
    today = datetime.today()
    
    # filttering the date and y_columns
    df_actual = df[[date_column, y_column, usd_myr_column]].copy()
    
    # generating the date list
    date_list = get_date_range(today, 45)
    
    # converting datetime to date for "Date" column
    df_actual[date_column] = df_actual[date_column].dt.date
    
    # We add new Column and fill value with "Past"
    df_actual["type"] = "Past"
    
    # creating the new dataframe and set the Date which we generated
    df_actual_prediction = pd.DataFrame({"Date": date_list})
    df_actual_prediction["prediction"] = lr_raw_prediction
    df_actual_prediction["live_prediction"] = predictions
       
    # creating the prediction data frame
    df_predicted = pd.DataFrame({ 
        date_column: date_list, 
        y_column: predictions,          
        usd_myr_column: usd_myr_price_list,
        "type": "Predicted"
    })

    # concating the multiple dataframe
    return pd.concat([df_actual, df_predicted]), df_actual_prediction

def custom_input_calculation(df,input_data, weighted_features_dict):
    counter = 0
    for key,custom_value in input_data.items():
        index_no = df.columns.get_loc(key)
        current_value = df.iloc[-1,index_no]
        if key in weighted_features_dict["ft_list_3"]:  # this is for increasing the weinght if malaysia palm stock in MT
            changed_value = current_value + (((custom_value*3)/100)*current_value)
            df.iloc[-1,index_no] = changed_value
            
        elif key in weighted_features_dict["ft_list_2"] :
            changed_value = current_value + (((custom_value*(2))/100)*current_value)
            df.iloc[-1,index_no] = changed_value
                
        elif key in weighted_features_dict["ft_list_1"]:   
            changed_value = current_value + ((custom_value/100)*current_value)
            df.iloc[-1,index_no] = changed_value   
        if current_value != changed_value:
            counter = counter + 1
    return df, counter            

def input_parameter_list(y_column,start_year, feature_list):
    df_final_pdesk, df_final_pdesk_2soyoil_arg, df_final_pdesk_3soyoil_arg, df_final_pdesk_daily =merge_daily_monthly_data()
    if y_column == "basis_spot(argentina)_future(3SoyoilCbot)":
        temp = df_final_pdesk_3soyoil_arg[df_final_pdesk_3soyoil_arg["Year"] >= start_year]
        last_row = temp.iloc[-1:].values.tolist()

    elif y_column == "basis_spot(argentina)_future(2SoyoilCbot)":
        temp = df_final_pdesk_2soyoil_arg[df_final_pdesk_2soyoil_arg["Year"] >= start_year]
        last_row = temp.iloc[-1:].values.tolist()
        
    else:
        temp = df_final_pdesk[df_final_pdesk['Year'] >= start_year]
        last_row = temp.iloc[-1:].values.tolist()
    input_dict = {}


    for key in feature_list:
        input_dict[key] = float(0) if np.isnan(temp.iloc[-1, temp.columns.get_loc(key)]) else float(temp.iloc[-1, temp.columns.get_loc(key)])

    return temp, last_row, input_dict, df_final_pdesk_daily

def decription(base64_message):
    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    return message

def getdata_from_s3_pp(dir_name, file_name):
    rows = get_data_from_query("SELECT * FROM auth_nobis").fetchall()
    access_key = decription(rows[0][0])
    secret_key = decription(rows[0][1])
    bucket_name = "public-posting"
    s3 = boto3.resource('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    bucket = s3.Bucket(bucket_name)
#     print(dir_name + file_name)
    for obj in bucket.objects.filter(Prefix=dir_name + file_name):
        dir_file = obj.get()['Body']
    return dir_file

# Revisit this to avoid calling s3 by using local data
def latest_posting_files(y_variable):
    date_key = common.today_date_key()
   
    df = get_cache(f"pdesk_what_if_latest_posting_df_{date_key}+{y_variable}")
    if(isinstance(df,pd.DataFrame) and len(df)>0):
        return df
    else:
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(Bucket='public-posting', Prefix='Pdesk/'+ y_variable)
        objects = sorted(response['Contents'], key=lambda obj: obj['LastModified'])
        ## Latest object
        latest_object = objects[-1]['Key']
        filename = latest_object[latest_object.rfind('/')+1:]
        df = pd.read_csv(getdata_from_s3_pp('Pdesk/'+y_variable+'/linear_regression/30-days-lookahead/',filename), index_col=[0])
        df['Date'] = pd.to_datetime(df['Date'])
        set_cache(f"pdesk_what_if_latest_posting_df_{date_key}_{y_variable}", df, expiry_time=settings.time_to_expire)
        return df

# run below cell for custom input
def calculate_what_if(key_y_column,feature_list,input_data,start_year, y_code, weighted_features_dict):
    lookahead_days = 8

    y_column = key_y_column
    # print(y_column)
    usd_myr_column = "USD_MYR_Price"
    
    temp, last_row, _, df_final_pdesk_daily  = input_parameter_list(key_y_column,start_year, feature_list)
    
    all_y_column = temp[[y_column]]
    
    
    all_lookahead_percentile = []
    
    today_date_str = datetime.today().strftime("%d_%m_%Y")
    
    # print("*****last row*****")
    # print( temp.iloc[-1:][['malaysia_palmoil_stock_in_MT', 'crude_oil_wti', 'sp500_close_index', 'Crude_Palm_Oil_Import_Duty_Value_Rupee_Per_MT',
    #     'soybeans_ending_stocks_current_month_estimate_wasde_MT', 'soybeans_ending_stocks_previous_month_estimate_wasde_MT']])

    # if y_column == 'mcx_spot_price':
    temp, counter = custom_input_calculation(temp, input_data, weighted_features_dict)
        
    # print("%%%%% last 2 rows %%%%%%")
    # print(temp.iloc[-2:][['malaysia_palmoil_stock_in_MT', 'crude_oil_wti', 'sp500_close_index', 'Crude_Palm_Oil_Import_Duty_Value_Rupee_Per_MT',
    #     'soybeans_ending_stocks_current_month_estimate_wasde_MT', 'soybeans_ending_stocks_previous_month_estimate_wasde_MT']])
    
    # this will store all the prediction for the n day
    predictions = []
    lr_raw_prediction = []
    usd_myr_price_list = []
    
    for day in range(1, lookahead_days + 1):
        date_column = "Date"
        x_column = get_feature_list_from_s3(key_y_column, day, is_3_month_active)
        # get prediction for the n days
        df_actual, prediction, lr_prediction, percentile_change = get_prediction(temp, x_column, y_column, day, all_y_column, is_3_month_active)        
        # storeing the prediction
        predictions.append(prediction[0])
        # storing the raw prediction
        # print(lr_prediction)
        lr_raw_prediction.append(lr_prediction)
        # storing the usd_myr_price
        usd_myr_price_list.append(df_actual[usd_myr_column].tail(1).values[0])
        # appending the dictionary lookahead and percentile change
        all_lookahead_percentile.append({ "Lookahead": str(day) + "_Lookahead", "percentile": percentile_change })
        
    df_final, df_actual_prediction = merge_prediction_dataframe(temp, y_column, usd_myr_column, day, predictions, usd_myr_price_list, lr_raw_prediction)
    df_final = df_final.sort_values('Date')
    df_final["moving_avg"] = df_final[y_column].rolling(7).mean()
    df_actual_prediction["moving_avg"] = df_final["moving_avg"].tail(day).values
    # we changing the predicted value with the moving average
    df_final[y_column] = np.where(df_final["type"] == "Predicted", df_final["moving_avg"], df_final[y_column])

    # sorting the value based on the date
    df_final = df_final.sort_values('Date')

    df_final = df_final.tail(150)
    
    
    # taking the latest posting data 
    posting = latest_posting_files(key_y_column)
    
    
    #taking only the predicted data from base prediction and what if prediction
    df_final_pred = df_final[df_final['type']=='Predicted']
    df_final_base = base_what_if(key_y_column)
    df_final_base_pred = df_final_base[df_final_base['type']=='Predicted']

    del df_final_pred['USD_MYR_Price']
    del df_final_pred['moving_avg']

    del df_final_base_pred['USD_MYR_Price']
    del df_final_base_pred['moving_avg']
    
    # merging only the base prediction and what if prediction data
    result = pd.merge(df_final_base_pred, df_final_pred, on="Date", how = 'left')
    result['Date'] = pd.to_datetime(result['Date'])  #necessary because after merging it changes to object type
    
    
    # merging the both predicted data(contains only 5 to 6 weeks ie only fridays data) with the posting data (posting data contains 30 day pred)
    result_final = pd.merge(posting, result, on="Date", how = 'outer')
    result_final = result_final.head(30)
    result_final = result_final.fillna(method='bfill')  # bffil because friday pred reflect the pred for current week not previous week
    result_final = result_final.fillna(method='ffill')  # its relevant but did it for precaution not to have nan values
        # clipping it to only 30 day 
    
    # delat is diffrence between the base pred minus what if pred
    # _x is for base because when merging two df with same column name the columns are renamed as _x and_y
    if(counter==0):
        result_final['delta'] = [0 for item in range(30)]
    else:
        result_final['delta'] = result_final[y_column + '_y'] - result_final[y_column + '_x']

        #if y_column == 'basis_spot(argentina)_future(3SoyoilCbot) 'or y_column == 'basis_spot(argentina)_future(2SoyoilCbot)' or y_column == 'basis_spot_future_bmd' or y_column == 'basis_spot_future_mcx':
    result_final['delta'] = result_final['delta'] * (-1)
    
    # subtracting the delat with the daily prediction 
    #     3_cpo_bmd_prices_USD_per_MT --> 3-CPO(BMD)_Prediction($/MT)
    #     bmd_spot_price -->  BMD_Prediction
    #     mcx_spot_price -->  MCX_Prediction
    #     3_soyoil_cbot_prices_USD_per_MT -->  Soyoil(CBOT)_Prediction
    #     2_soyoil_cbot_prices_USD_per_MT -->  Soyoil(CBOT)_Prediction
    #     soyoil_ncdex_spot_price -->    Soyoil(NCDEX)_Prediction
    if y_column == '3_cpo_bmd_prices_USD_per_MT':        
        result_final['what_if_change'] = result_final['3-CPO(BMD)_Prediction($/MT)'] - result_final['delta']
        
    elif y_column == 'bmd_spot_price':        
        result_final['what_if_change'] = result_final['BMD_Prediction'] - result_final['delta']
        
    elif y_column == 'mcx_spot_price':        
        result_final['what_if_change'] = result_final['MCX_Prediction'] - result_final['delta']
        
    elif y_column == 'soyoil_ncdex_spot_price':        
        result_final['what_if_change'] = result_final['Soyoil(NCDEX)_Prediction'] - result_final['delta']
        
    elif y_column == '3_soyoil_cbot_prices_USD_per_MT' or y_column == '2_soyoil_cbot_prices_USD_per_MT':        
        result_final['what_if_change'] = result_final['Soyoil(CBOT)_Prediction'] - result_final['delta']
        
    elif y_column == 'Argentina_Soyoil':        
        result_final['what_if_change'] = result_final['Argentina-Soyoil_Prediction'] - result_final['delta']

    elif y_column == 'basis_spot(argentina)_future(3SoyoilCbot)':        
        result_final['what_if_change'] = result_final['Basis-Argentina-Soyoil-3Soyoil(CBOT)_Prediction'] + result_final['delta']
        
    elif y_column == 'basis_spot(argentina)_future(2SoyoilCbot)':        
        result_final['what_if_change'] = result_final['Basis-Argentina-Soyoil-2Soyoil(CBOT)_Prediction'] + result_final['delta']
        
    elif y_column == 'basis_spot_future_bmd':
        result_final['what_if_change'] = result_final['Basis_MalaysiaCPOSpot_3CPO(BMD)_Prediction'] + result_final['delta']
        
    elif y_column == 'basis_spot_future_mcx':
        result_final['what_if_change'] = result_final['Basis_IndiaCPOSpot_3CPO(BMD)_Prediction'] + result_final['delta']
        
    elif y_column == 'RBD_PalmOlein_Kandla_USD_per_MT':
        result_final['what_if_change'] = result_final['RBD-Palmolein-Kandla_Prediction'] + result_final['delta']
    
    # df_final_pdesk_daily = df_final_pdesk.copy()
    # df_final_pdesk_daily is used to get the past data for y_variable aka commodity to plt on graph

    if y_column == 'basis_spot(argentina)_future(2SoyoilCbot)':
        _, df_final_pdesk_2soyoil_arg, _, _   = merge_daily_monthly_data()
        df_final_pdesk_daily1 = df_final_pdesk_2soyoil_arg[['Date', y_column]]
        df_final_pdesk_daily2 = df_final_pdesk_daily1.tail(100)


    elif y_column == 'basis_spot(argentina)_future(3SoyoilCbot)':
        _, _, df_final_pdesk_3soyoil_arg, _   = merge_daily_monthly_data()
        df_final_pdesk_daily1 = df_final_pdesk_3soyoil_arg[['Date', y_column]]
        df_final_pdesk_daily2 = df_final_pdesk_daily1.tail(100)

    else:
        df_final_pdesk_daily1 = df_final_pdesk_daily[['Date', y_column]]
        df_final_pdesk_daily2 = df_final_pdesk_daily1.tail(100)
    
    
    # after merging the past data with what if change to get fianl df to be plotted
    final = pd.merge(df_final_pdesk_daily2, result_final, on="Date", how = 'outer')
    final.sort_values(by='Date', ascending=True)
    final = final.tail(150)
    

    # need to revisit in future  
    final['type_x'] = final['type_x'].fillna("Past")
    #setting the last row after prediction to todays value
    x_past_date = (final.loc[final['type_x'] == "Past"]["Date"]).dt.strftime('%d-%m-%Y').tolist()
    x_predicted_date = (final.loc[final['type_x'] == "Predicted"]["Date"]).dt.strftime('%d-%m-%Y').tolist()
    y_past = final.loc[final['type_x'] == "Past"][key_y_column].astype('float').tolist()
    y_predicted = final.loc[final['type_x'] == "Predicted"][y_code].astype('float').tolist()
    what_if_change = final.loc[final['type_x'] == "Predicted"]["what_if_change"].astype('float').tolist()
    final_chart_data = FinalChartData(data=[
                                ScatterChart(x=x_past_date,y=y_past,name="past"),
                                ScatterChart(x=x_predicted_date,y=y_predicted,name="predicted"),
                                ScatterChart(x=x_predicted_date,y=what_if_change,name="what-if"),    
                            ])
    # print("reset last row after the user has input the data and predition was made ")
    temp.drop(temp.tail(1).index,inplace=True) # drop last 1 rows
    temp.loc[len(temp.index)] = last_row[0]
    # print(temp.iloc[-1:][['malaysia_palmoil_stock_in_MT', 'crude_oil_wti', 'sp500_close_index', 'Crude_Palm_Oil_Import_Duty_Value_Rupee_Per_MT',
    #     'soybeans_ending_stocks_current_month_estimate_wasde_MT', 'soybeans_ending_stocks_previous_month_estimate_wasde_MT']])
    
    return final_chart_data
