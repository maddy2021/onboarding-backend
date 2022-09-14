import pandas as pd
from app.core.config import settings
from app.schemas.pdesk import BarChart, FinalChartData

def explaninalibility(y_variable, l_days):
    rename_ft = {'3_cpo_bmd_prices_USD_per_MTactual_x_train': 'CPO(BMD)-Prices',
             '2_po_dce_prices_USD_per_MT': 'Palm-Olein-Dalian-Price',
             'SMA_7_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-1',
             'bmd_spot_price': 'Malaysia-CPO-Spot-Price',
             'RSI_7_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-4',
             'EMA_7_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-2',
             'Crude_Palm_Oil_Import_Duty_Value_Rupee_Per_MT': 'India-CPO-Import-Duty',
             '3_cpo_bmd-2_soyoil_cbot_prices_USD_per_MT': 'Palm-Soy-Spread',
             'crude_oil_wti': 'Crude-Oil-Price',
             'third_month_future_volume_soybean_cbot_in_MT': 'CBOT-Volume',
             'third_month_future_volume_bmd_in_MT': 'BMD-Volume',
             'malaysia_palmoil_stock_in_MT': 'MPOB-Palm-Oil-Stock',
             '2_soyoil_cbot_prices_USD_per_MT': 'Soyoil(CBOT)-Price',
             'ROC_7_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-3',
             'USD_MYR_Price': 'Forex-Prices',
             'mcx_spot_price': 'India-CPO-Spot-Price',
             'basis_spot_future_bmdactual_x_train': 'Basis-MalaysiaCPOSpot-3CPO(BMD)',
             'basis_spot_future_mcxactual_x_train': 'Basis-IndiaCPOSpot-3CPO(BMD)',
             'SMA_15_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-1',
             'EMA_15_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-2',
             'ROC_15_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-3',
             'RSI_15_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-4',
             'EMA_30_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-2',
             'SMA_30_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-1',
             'ROC_30_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-3',
             'RSI_30_3_cpo_bmd_prices_USD_per_MT': 'Tech-Feature-4',
             'SMA_7_bmd_spot_price': 'Tech-Feature-1',
             'SMA_15_bmd_spot_price': 'Tech-Feature-1',
             'SMA_30_bmd_spot_price': 'Tech-Feature-1',
             'EMA_7_bmd_spot_price': 'Tech-Feature-2',
             'EMA_15_bmd_spot_price': 'Tech-Feature-2',
             'EMA_30_bmd_spot_price': 'Tech-Feature-2',
             'ROC_7_bmd_spot_price': 'Tech-Feature-3',
             'ROC_15_bmd_spot_price': 'Tech-Feature-3',
             'ROC_30_bmd_spot_price': 'Tech-Feature-3',
             'RSI_7_bmd_spot_price': 'Tech-Feature-4',
             'RSI_15_bmd_spot_price': 'Tech-Feature-4',
             'RSI_30_bmd_spot_price': 'Tech-Feature-4',
             'SMA_7_basis_spot_future_bmd': 'Tech-Feature-1',
             'SMA_15_basis_spot_future_bmd': 'Tech-Feature-1',
             'SMA_30_basis_spot_future_bmd': 'Tech-Feature-1',
             'EMA_7_basis_spot_future_bmd': 'Tech-Feature-2',
             'EMA_15_basis_spot_future_bmd': 'Tech-Feature-2',
             'EMA_30_basis_spot_future_bmd': 'Tech-Feature-2',
             'ROC_7_basis_spot_future_bmd': 'Tech-Feature-3',
             'ROC_15_basis_spot_future_bmd': 'Tech-Feature-3',
             'ROC_30_basis_spot_future_bmd': 'Tech-Feature-3',
             'RSI_7_basis_spot_future_bmd': 'Tech-Feature-4',
             'RSI_15_basis_spot_future_bmd': 'Tech-Feature-4',
             'RSI_30_basis_spot_future_bmd': 'Tech-Feature-4',
             'SMA_7_basis_spot_future_mcx': 'Tech-Feature-1',
             'SMA_15_basis_spot_future_mcx': 'Tech-Feature-1',
             'SMA_30_basis_spot_future_mcx': 'Tech-Feature-1',
             'EMA_7_basis_spot_future_mcx': 'Tech-Feature-2',
             'EMA_15_basis_spot_future_mcx': 'Tech-Feature-2',
             'EMA_30_basis_spot_future_mcx': 'Tech-Feature-2',
             'ROC_7_basis_spot_future_mcx': 'Tech-Feature-3',
             'ROC_15_basis_spot_future_mcx': 'Tech-Feature-3',
             'ROC_30_basis_spot_future_mcx': 'Tech-Feature-3',
             'RSI_7_basis_spot_future_mcx': 'Tech-Feature-4',
             'RSI_15_basis_spot_future_mcx': 'Tech-Feature-4',
             'RSI_30_basis_spot_future_mcx': 'Tech-Feature-4',
             'bmd_spot_priceactual_x_train': 'BMD-spot-price',
             'Argentina_Soyoil': 'Argentina-Soyoil-Prices',
             'SMA_7_temperature_index': 'Tech-Feature-Temp-1',
             'SMA_15_temperature_index': 'Tech-Feature-Temp-1',
             'SMA_30_temperature_index': 'Tech-Feature-Temp-1',
             'EMA_7_temperature_index': 'Tech-Feature-Temp-2',
             'EMA_15_temperature_index': 'Tech-Feature-Temp-2',
             'EMA_30_temperature_index': 'Tech-Feature-Temp-2',
             'ROC_7_temperature_index': 'Tech-Feature-Temp-3',
             'ROC_15_temperature_index': 'Tech-Feature-Temp-3',
             'ROC_30_temperature_index': 'Tech-Feature-Temp-3',
             'RSI_7_temperature_index': 'Tech-Feature-Temp-4',
             'RSI_15_temperature_index': 'Tech-Feature-Temp-4',
             'RSI_30_temperature_index': 'Tech-Feature-Temp-4',
             'SMA_7_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-1',
             'SMA_15_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-1',
             'SMA_30_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-1',
             'EMA_7_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-2',
             'EMA_15_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-2',
             'EMA_30_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-2',
             'ROC_7_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-3',
             'ROC_15_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-3',
             'ROC_30_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-3',
             'RSI_7_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-4',
             'RSI_15_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-4',
             'RSI_30_third_month_future_volume_bmd_in_MT': 'Tech-Volume-Feature-4',
             'Argentina_Soyoil_minus_Malaysia_CPO_Spot': 'Argentina-Basis-Feature',
             'SMA_7_precipitation_index': 'Tech-Feature-Precipitaion-1',
             'SMA_15_precipitation_index': 'Tech-Feature-Precipitaion-1',
             'SMA_30_precipitation_index': 'Tech-Feature-Precipitaion-1',
             'EMA_7_precipitation_index': 'Tech-Feature-Precipitaion-2',
             'EMA_15_precipitation_index': 'Tech-Feature-Precipitaion-2',
             'EMA_30_precipitation_index': 'Tech-Feature-Precipitaion-2',
             'ROC_7_precipitation_index': 'Tech-Feature-Precipitaion-3',
             'ROC_15_precipitation_index': 'Tech-Feature-Precipitaion-3',
             'ROC_30_precipitation_index': 'Tech-Feature-Precipitaion-3',
             'RSI_7_precipitation_index': 'Tech-Feature-Precipitaion-4',
             'RSI_15_precipitation_index': 'Tech-Feature-Precipitaion-4',
             'RSI_30_precipitation_index': 'Tech-Feature-Precipitaion-4',
             '3_cpo_bmd_prices_USD_per_MT': 'CPO(BMD)-Prices',
             'usa_production_soyoil_in_MT': 'USA Soyoil Production',
             'usa_soyoil_exports_in_MT': 'Soyoil(CBOT) Price',
             '3_cpo_bmd-3_soyoil_cbot_prices_USD_per_MT': 'Palm-Soy-Spread',
             '3_soyoil_cbot_prices_USD_per_MT': 'Soyoil(CBOT) Price',
             'cdsbo_india_portstock': 'CDSBO-india-portstock',
             'total_palm_india_portstock': 'Total-palm-india-portstock',
             'sp500_close_index': 'S & P500'}

    temp_df_exp = pd.read_csv(
        settings.DATA_FILE_PATH+"/Pdesk/static_features_temp/" + y_variable + "/" + str('linear_regression') + "/" + str(
            l_days) + "_lookahead_days/" + str(2018) + "/model_output_coefficient.csv", index_col=[0])
    temp_df_exp = temp_df_exp.sort_values('coefficient_in_per', ascending=False)
    temp_df_exp = temp_df_exp.reset_index(drop=True)
    feature_list = []
    for item in temp_df_exp['feature_name']:
        if item in rename_ft.keys():
            feature_list.append(rename_ft[item])
    temp_df_exp['feature_rename'] = feature_list
    return temp_df_exp , l_days

def get_explainable_graph_data(y_variable,l_days, is_internal):
    df,_ = explaninalibility(y_variable,l_days)
    if(is_internal):
        x= df["feature_name"].tolist()
    else: 
        x=df["feature_rename"].tolist()
    y=df["final_coefficient_in_per"].tolist()
    return FinalChartData(data = [BarChart(x=x,y=y)])
