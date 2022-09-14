from app.helpers.pdesk.backtest.public_posting_helper import public_posting_init
from app.schemas.pdesk import BarChart, BoxChart, FinalChartData
from app.util.query import get_table_columns, get_table_data
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
pd.set_option('mode.use_inf_as_na', True)
import numpy as np
from app.core.config import settings

from collections import OrderedDict
import glob
import math
from datetime import timedelta


def unique_lst(list1):
    # print('@@13')
    x = np.array(list1)
    return list((np.unique(x)))

def function_for_startandend_monthandyear(y_variable):
    # this function will return the month and year for a particular y_variable that will be used in chained callback
    # print("@@14")
    list_date = []
    list_month = []
    list_year = []
    all_date_and_year = []

    if y_variable == '2-3_soyoil_cbot_prices_USD_per_MT':
        for variable_2_3cbot in ['2_soyoil_cbot_prices_USD_per_MT', '3_soyoil_cbot_prices_USD_per_MT']:
            for file_name in glob.iglob(settings.DATA_FILE_PATH+r"/Pdesk/Public_posting/" + variable_2_3cbot + "/linear_regression/30-days-lookahead/*.csv", recursive=True):
                # print("file names ", file_name)
                date_and_year = str(file_name).split('lookahead-')[-1][:10]
                date_and_year_list = str(date_and_year).split('_')
                # print("date and year list ", date_and_year_list)
                all_date_and_year.append(date_and_year)
                list_date.append(date_and_year_list[0])
                # print(date_and_year_list[1])
                list_month.append(date_and_year_list[1])
                list_year.append(date_and_year_list[2])
        return unique_lst(list_date), unique_lst(list_month), unique_lst(list_year), all_date_and_year
    else:
        # print("first for dir corr")
        # print("first for abs delta")
        for file_name in glob.iglob(settings.DATA_FILE_PATH+r"/Pdesk/Public_posting/" + y_variable + "/linear_regression/30-days-lookahead/*.csv", recursive=True):
            # print("file names ",file_name)
            date_and_year = str(file_name).split('lookahead-')[-1][:10]
            date_and_year_list = str(date_and_year).split('_')
            # print("date and year list ",date_and_year_list)
            all_date_and_year.append(date_and_year)
            list_date.append(date_and_year_list[0])
            # print(date_and_year_list[1])
            list_month.append(date_and_year_list[1])
            list_year.append(date_and_year_list[2])
        return unique_lst(list_date), unique_lst(list_month), unique_lst(list_year), all_date_and_year


def getting_publicposting_files_auto(y_variable, month, year,y_label,months_dict):
    # print("@@15")

    '''
    This function read all the csv's for a particular y_variable and a particular month.
    And in the process it will create date, date of posting, lookahead days, y_shifted, y_unshifted.
    y_prediction we will get from csv's. Y_shifted and y_unshifted we will get from df_final_df. So we need to merge two df's.

    '''
    df_final_pdesk = public_posting_init()
    variable = {'3_cpo_bmd_prices_USD_per_MT': '3-CPO-(BMD)',
                '3_soyoil_cbot_prices_USD_per_MT': 'Soyoil-(CBOT)',
                '2_soyoil_cbot_prices_USD_per_MT': 'Soyoil-(CBOT)',
                'soyoil_ncdex_spot_price': 'Soyoil-(NCDEX)',
                'bmd_spot_price': 'BMD',
                'mcx_spot_price': 'MCX',
                'basis_spot_future_bmd': 'Basis-Malaysia-Spot-3CPO(BMD)',
                'basis_spot_future_mcx': 'Basis-India(MCX)-Spot-3CPO(BMD)'}
    y_label = variable[y_variable]
    months = dict((reversed(item) for item in months_dict.items()))
    blank_df = pd.DataFrame()  # this df is being used to stack merged df
    stacked_mereged_df_2 = pd.DataFrame()  # this df is used for merging 2_soyoil_cbot_prices_USD_per_MT
    stacked_mereged_df_3 = pd.DataFrame()  # this df is used for merging 3_soyoil_cbot_prices_USD_per_MT

    blank_df = pd.DataFrame()  # this df is being used to stack merged df
    # this df is used for merging 2_soyoil_cbot_prices_USD_per_MT
    stacked_mereged_df_2 = pd.DataFrame()
    # this df is used for merging 3_soyoil_cbot_prices_USD_per_MT
    stacked_mereged_df_3 = pd.DataFrame()
    mereged_df_2_3 = df_final_pdesk['2_soyoil_cbot_prices_USD_per_MT'].combine_first(
        df_final_pdesk['3_soyoil_cbot_prices_USD_per_MT'])
    df_final_pdesk['2-3_soyoil_cbot_prices_USD_per_MT'] = mereged_df_2_3
    df_daily_for_renaming_2 = df_final_pdesk[[
        'Date', '2-3_soyoil_cbot_prices_USD_per_MT']]
    df_daily_for_renaming_3 = df_final_pdesk[[
        'Date', '2-3_soyoil_cbot_prices_USD_per_MT']]

    if month == "January":
        month_to_iterate = ['11', '12', '01']
    elif month == "February":
        month_to_iterate = ['12', '01', '02']
    else:
        # in the below code we gettign the list of months for which we need ti iterate over (at max 3)
        month_to_iterate = [str(0) + str(month_num) if len(str(month_num)) != 2 else str(month_num) for month_num in
                            range(int(months[month]) - 2, int(months[month]) + 1)]
    # print(month_to_iterate)

    blank_df = pd.DataFrame()

    if y_variable == '2-3_soyoil_cbot_prices_USD_per_MT':
        for month in month_to_iterate:
            for variable_2_3cbot in ['2_soyoil_cbot_prices_USD_per_MT', '3_soyoil_cbot_prices_USD_per_MT']:
                for date in range(1, 32):  # this loop is for looping over the date
                    try:
                        try:
                            if date <= 9:
                                date = str(0) + str(date)

                            temp = pd.read_csv(
                                settings.DATA_FILE_PATH+"/Pdesk/Public_posting/" + variable_2_3cbot + "/linear_regression/30-days-lookahead/" +
                                "public-posting-pdesk-30-days-lookahead-"
                                + str(date) + "_" +
                                month + "_" +
                                str(year) + "-" +
                                y_label + ".csv"
                            )

                            # print("the files being read")
                            # print("Pdesk/" + variable_2_3cbot + "/linear_regression/30-days-lookahead/",
                            # "public-posting-pdesk-30-days-lookahead-" + str(date) + "_" + month + "_" + str(
                            #     2022) + "-" + variable[variable_2_3cbot] + ".csv")
                            temp['lookahead_days'] = ['lookahead_day_' + str(i) for i in
                                                      range(1, len(temp) + 1)]  # creating lookahead days
                            # changing the date to datetime
                            temp["Date"] = pd.to_datetime(temp["Date"])
                            temp.sort_values(by=['Date'])
                            date_of_posting = str(2022) + "-" + month + "-" + str(
                                date)  # creating date of posting to use it in getting the unshifted date
                            # print("date of posting", date_of_posting)
                            temp["Date_of_posting"] = [date_of_posting for i in
                                                       range(30)]  # adding the date of posting column
                            temp["Date_of_posting"] = pd.to_datetime(
                                temp["Date_of_posting"])  # changing date of posting column to datetime
                            temp.sort_values(by=['Date_of_posting'])
                            # selecting the date of posting
                            date_of_posting = temp["Date_of_posting"][0]
                            # print("date of posting------", date_of_posting)
                            unshifted_date = date_of_posting - timedelta(
                                days=1)  # creating un_shifted date i,e the previous date (for days on which we have holidays the un_shifted date will only look back for max of 4 days, code in below while loop)
                            # print("unshifted date of posting", unshifted_date)
                            unshifted_date_constant = unshifted_date

                            # in the below while loop, checking if the y_unshifted is present the previous day (in case where we are makaing posting
                            # on mondays and then the y_unshifted will be available on friday as on saturday and sunday we dont get data,
                            # so in the logic we will look at maximun of 4 days back to get y_unshifted)

                            # here setting the difference between shifted and  unshifted to 2
                            diff_shifted_and_unshifted_date = 1
                            # here checking if the difference between shifted and  unshifted is less than equal to 4
                            while diff_shifted_and_unshifted_date <= 4:
                                if len(list(df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][
                                    [variable_2_3cbot]].values)) == 0 or math.isnan(
                                        df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][
                                            [variable_2_3cbot]].values):
                                    # checking if df_final_pdesk contains the scrapped data for the particular unshifted date or for nan values for that particular days
                                    # print('********************')
                                    # print("unshifted_date not in pdeskfinal", unshifted_date.date())
                                    unshifted_date = unshifted_date_constant - timedelta(
                                        days=diff_shifted_and_unshifted_date)  # if we dont have the scrapped data for that particular date we look for scrapped 2 days ago

                                    if len(list(df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][[
                                            variable_2_3cbot]].values)) != 0:  # if we have scrapped data 2 days ago we use it
                                        value_of_y_unshifted = float(
                                            df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][
                                                variable_2_3cbot].values)
                                        # print("unshifted_date not in pdeskfinal", unshifted_date.date())
                                        # print('value_of_y_unshifted', value_of_y_unshifted)
                                        temp['y_unshifted'] = [
                                            value_of_y_unshifted for i in range(30)]
                                        diff_shifted_and_unshifted_date = 5  # for coming out of while loop
                                    else:
                                        print()
                                    # if we dont have scappred data we will look for it again a day before
                                    diff_shifted_and_unshifted_date += 1
                                    # print('Inside if date diff_shifted_and_unshifted_date',
                                    #       diff_shifted_and_unshifted_date)
                                else:

                                    value_of_y_unshifted = float(
                                        df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][variable_2_3cbot].values)
                                    # print('value_of_y_unshifted', value_of_y_unshifted)
                                    temp['y_unshifted'] = [
                                        value_of_y_unshifted for i in range(30)]
                                    diff_shifted_and_unshifted_date = 5  # for coming out of while loop

                        except TypeError:  # this try except block will ignore the posting values if we are not able to find the scrapped value in the past 4 days
                            continue

                        # below if statements are added to have uniform column in merged_df( because there is one csv where the column is
                        # diffrent from other for each y_variable) and
                        # for creating seperate merged and stacked df for 2 soyoil and 3 soyoil

                        if 'Soyoil-(CBOT)' in temp.columns:
                            temp.rename(
                                columns={'Soyoil-(CBOT)': 'Soyoil(CBOT)_Prediction'}, inplace=True)

                        if variable_2_3cbot == '2_soyoil_cbot_prices_USD_per_MT':
                            mereged_df_2 = pd.merge(temp, df_daily_for_renaming_2[
                                ['Date', '2-3_soyoil_cbot_prices_USD_per_MT']], on='Date')
                            mereged_df_2.rename(columns={'2-3_soyoil_cbot_prices_USD_per_MT': 'Soyoil_shifted'},
                                                inplace=True)
                            stacked_mereged_df_2 = pd.concat(
                                [stacked_mereged_df_2, mereged_df_2], axis=0)
            
                        if variable_2_3cbot == '3_soyoil_cbot_prices_USD_per_MT':
                            mereged_df_3 = pd.merge(temp, df_daily_for_renaming_3[
                                ['Date', '2-3_soyoil_cbot_prices_USD_per_MT']], on='Date')
                            mereged_df_3.rename(columns={'2-3_soyoil_cbot_prices_USD_per_MT': 'Soyoil_shifted'},
                                                inplace=True)
                            stacked_mereged_df_3 = pd.concat(
                                [stacked_mereged_df_3, mereged_df_3], axis=0)
            
                    except FileNotFoundError:  # this try except block is because for dates where we dont have posting it will skip
                        continue

                # in the below if conditions concatenating the 2 syoil and 3 soyoil into 1 df

                if len(stacked_mereged_df_2) > 0 and len(stacked_mereged_df_3) > 0:
                    blank_df = pd.concat(
                        [blank_df, stacked_mereged_df_2, stacked_mereged_df_3], axis=0)

                elif len(stacked_mereged_df_2) > 0 and len(stacked_mereged_df_3) == 0:
                    blank_df = pd.concat([blank_df, stacked_mereged_df_2], axis=0)

                elif len(stacked_mereged_df_3) > 0 and len(stacked_mereged_df_2) == 0:
                    blank_df = pd.concat([blank_df, stacked_mereged_df_3], axis=0)

        blank_df['month_for_which_prediction_was_made'] = pd.DatetimeIndex(
            blank_df['Date']).month
        blank_df = blank_df[blank_df['month_for_which_prediction_was_made'] == int(
            month_to_iterate[-1])]
        blank_df.drop_duplicates(inplace=True)
        blank_df.rename(
            columns={'Date': 'Date_for_which_prediction_was_made'}, inplace=True)
        return blank_df

    else:

        for month in month_to_iterate:
            for date in range(1, 32):  # this loop is for looping over the date

                try:
                    try:
                        if date <= 9:
                            date = str(0) + str(date)

                        temp = pd.read_csv(
                            settings.DATA_FILE_PATH+"/Pdesk/Public_posting/" + y_variable + "/linear_regression/30-days-lookahead/" +
                            "public-posting-pdesk-30-days-lookahead-"
                            + str(date) + "_" +
                            month + "_" +
                            str(year) + "-" +
                            y_label + ".csv"
                        )

                        # print("the files being read")
                        # print("Pdesk/" + y_variable + "/linear_regression/30-days-lookahead/",
                        #       "public-posting-pdesk-30-days-lookahead-" + str(date) + "_" + month + "_" + str(
                        #           2022) + "-" + variable[y_variable] + ".csv")
                        temp['lookahead_days'] = ['lookahead_day_' + str(i) for i in
                                                  range(1, len(temp) + 1)]  # creating lookahead days
                        # changing the date to datetime
                        temp["Date"] = pd.to_datetime(temp["Date"])
                        temp.sort_values(by=['Date'])
                        date_of_posting = str(2022) + "-" + month + "-" + str(
                            date)  # creating date of posting to use it in getting the unshifted date
                        # print("date of posting", date_of_posting)
                        temp["Date_of_posting"] = [date_of_posting for i in
                                                   range(30)]  # adding the date of posting column
                        temp["Date_of_posting"] = pd.to_datetime(
                            temp["Date_of_posting"])  # changing date of posting to datetime
                        temp.sort_values(by=['Date_of_posting'])
                        # selecting the date of posting
                        date_of_posting = temp["Date_of_posting"][0]
                        # print("date of posting------", date_of_posting)
                        unshifted_date = date_of_posting - timedelta(
                            days=1)  # creating un_shifted date i,e the previous date (for days on which we have holidays the un_shifted date will only look back for max of 4 days, code in below while loop)
                        # print("unshifted date of posting", unshifted_date)
                        unshifted_date_constant = unshifted_date

                        # in the below while loop, checking if the y_unshifted is present the previous day (in case where we are makaing posting
                        # on mondays and then the y_unshifted will be available on friday as on saturday and sunday we dont get data,
                        # so in the logic we will look at maximun of 4 days back to get y_unshifted)

                        # here setting the difference between shifted and  unshifted to 2
                        diff_shifted_and_unshifted_date = 1
                        # here checking if the difference between shifted and  unshifted is less than equal to 4
                        while diff_shifted_and_unshifted_date <= 4:
                            if len(list(df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][
                                [y_variable]].values)) == 0 or math.isnan(
                                    df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][[y_variable]].values):
                                # checking if df_final_pdesk contains the scrapped data for the particular unshifted date or for nan values for that particular days
                                # print('********************')
                                # print("unshifted_date not in pdeskfinal", unshifted_date.date())
                                unshifted_date = unshifted_date_constant - timedelta(
                                    days=diff_shifted_and_unshifted_date)  # if we dont have the scrapped data for that particular date we look for scrapped 2 days ago

                                if len(list(df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][[
                                        y_variable]].values)) != 0:  # if we have scrapped data 2 days ago we use it
                                    value_of_y_unshifted = float(
                                        df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][y_variable].values)
                                    # print("unshifted_date not in pdeskfinal", unshifted_date.date())
                                    # print('value_of_y_unshifted', value_of_y_unshifted)
                                    temp['y_unshifted'] = [
                                        value_of_y_unshifted for i in range(30)]
                                    diff_shifted_and_unshifted_date = 5  # for coming out of while loop
                                else:
                                    print()
                                # if we dont have scappred data we will look for it again a day before
                                diff_shifted_and_unshifted_date += 1
                                # print('Inside if date diff_shifted_and_unshifted_date', diff_shifted_and_unshifted_date)
                            else:

                                value_of_y_unshifted = float(
                                    df_final_pdesk[df_final_pdesk['Date'] == unshifted_date][y_variable].values)
                                # print('value_of_y_unshifted', value_of_y_unshifted)
                                temp['y_unshifted'] = [
                                    value_of_y_unshifted for i in range(30)]
                                diff_shifted_and_unshifted_date = 5  # for coming out of while loop

                    except TypeError:  # this try except block will ignore the posting values if we are not able to find the scrapped value in the past 4 days
                        continue

                    # merging the temp_df(it contains- Date, date of posting, lookahead_days, y_unshifted, y_prediction) and df_final_pdesk (it contains - Date and y_variable) on date
                    mereged_df = pd.merge(temp, df_final_pdesk[['Date', y_variable]],
                                          on='Date')  # after getting the merged df
                    # print(mereged_df)

                    # below if statements are added to have uniform column in merged_df( because there is one csv where the column is
                    # diffrent from other for each y_variable)

                    # checked for date 24-02-2022 3-CPO-(BMD) 3-CPO(BMD)_Prediction($/MT), y_variable - 3_cpo_bmd_prices_USD_per_MT
                    if '3-CPO-(BMD)' in mereged_df.columns:
                        mereged_df.rename(
                            columns={'3-CPO-(BMD)': '3-CPO(BMD)_Prediction($/MT)'}, inplace=True)

                    if 'BMD' in mereged_df.columns:
                        mereged_df.rename(
                            columns={'BMD': 'BMD_Prediction'}, inplace=True)

                    if 'MCX' in mereged_df.columns:
                        mereged_df.rename(
                            columns={'MCX': 'MCX_Prediction'}, inplace=True)

                    if 'Soyoil-(NCDEX)' in mereged_df.columns:
                        mereged_df.rename(
                            columns={'Soyoil-(NCDEX)': 'Soyoil(NCDEX)_Prediction'}, inplace=True)

                    # finally concatenating the merged df to black_df to get the whole df for a particular y_variable and month

                    blank_df = pd.concat([blank_df, mereged_df], axis=0)
                    # print("lenght of blank_df ", len(blank_df))
                except FileNotFoundError:  # this try except block is because for dates where we dont have posting it will skip
                    continue

        blank_df['month_for_which_prediction_was_made'] = pd.DatetimeIndex(
            blank_df['Date']).month
        blank_df = blank_df[blank_df['month_for_which_prediction_was_made'] == int(
            month_to_iterate[-1])]
        blank_df.drop_duplicates(inplace=True)
        blank_df.rename(
            columns={'Date': 'Date_for_which_prediction_was_made'}, inplace=True)
        # print("printing blank df")
        # print(blank_df)
        return blank_df

def plot_dir_corr_auto(y_variable, month, year, val_per,y_label,months_dict, y_code):
    df_op= getting_publicposting_files_auto(y_variable, month, year,y_label,months_dict)
    
    df_op.rename(columns={y_code: 'y_prediction', y_variable: 'y_shifted'},inplace=True)

    df_op = df_op.reset_index()

    # calcutaing the percentage change
    df_op['pct_change'] = ((df_op['y_shifted'] - df_op['y_unshifted']) / df_op['y_unshifted']) * 100
    df_op['abs_pct_change'] = df_op['pct_change'].abs()

    # filtering based onthe percentage change
    df_op = df_op.loc[df_op['abs_pct_change'] > val_per]
    df_op = df_op.reset_index()

    actual_direction = []
    pred_direction = []
    directional_correctness = []

    for i in range(len(df_op['y_shifted'])):
        # actual direction
        if (df_op['y_unshifted'][i] < df_op['y_shifted'][i]):
            actual_direction.append(1)
        else:
            actual_direction.append(0)

        # prediction direction
        if df_op['y_unshifted'][i] < df_op['y_prediction'][i]:
            pred_direction.append(1)
        else:
            pred_direction.append(0)

    for i in range(len(pred_direction)):
        if pred_direction[i] == 0 and actual_direction[i] == 0:
            directional_correctness.append(1)
        elif pred_direction[i] == 1 and actual_direction[i] == 1:
            directional_correctness.append(1)
        else:
            directional_correctness.append(0)

    df_op['actual_direction'] = actual_direction
    df_op['pred_direction'] = pred_direction
    df_op['directional_correctness'] = directional_correctness

    dir_value = []
    list_dir = [(j + 1) for j in range(30)]
    number_of_samples = []

    for i in range(1, 31):
        temp_df = df_op[df_op['lookahead_days'] == 'lookahead_day_' + str(i)]
        number_of_samples.append(len(temp_df))
        ones = len(temp_df[(temp_df['directional_correctness'] == 1) & (
                    temp_df['lookahead_days'] == 'lookahead_day_' + str(i))])
        if len(temp_df[temp_df['lookahead_days'] == 'lookahead_day_' + str(i)]) == 0:
            dir_value.append(0)
        else:
            dir_per = round((ones / len(temp_df[temp_df['lookahead_days'] == 'lookahead_day_' + str(i)])) * 100, 2)
            dir_value.append(dir_per)


    # Create DataFrame
    df = pd.DataFrame()
    df['directional_corretness'] = dir_value
    df['lookahead_days'] = list_dir
    df['number_of_samples'] = number_of_samples

    return df

def update_directional_correctness(df_dir_corr_data, y_variable, y_label, high_impact_cases):
    # print("@@17")

    if y_variable == '3_cpo_bmd_prices_USD_per_MT':
        posting_starting_date = '24-02-2022'
    elif y_variable == 'basis_spot_future_bmd' or y_variable == 'basis_spot_future_mcx':
        posting_starting_date = '02-03-2022'
    elif y_variable == 'bmd_spot_price' or y_variable == 'mcx_spot_price' or y_variable == 'soyoil_ncdex_spot_price':
        posting_starting_date = '24-02-2022'
    elif y_variable == '2-3_soyoil_cbot_prices_USD_per_MT':
        posting_starting_date = '24-02-2022'
    else:
        posting_starting_date = 'Updating'

    date_list = []
    month_list = []
    year_list = []
    date, month, year, all_date_and_year = function_for_startandend_monthandyear(y_variable)
    for ele in all_date_and_year:
        date_list.append(ele[:2])
        month_list.append(ele[3:5])
        year_list.append(ele[6:])

    v = []

    for i in range(len(date_list)):
        s = str(year_list[i]) + '-' + str(month_list[i]) + '-' + str(date_list[i])
        v.append(s)
    latest_posting_date = max(v)

    df_dir_corr_data['lookahead_days'] = df_dir_corr_data['lookahead_days'].astype(str)
    lookahead_days = df_dir_corr_data['lookahead_days'].tolist()
    directional_corretness=  df_dir_corr_data['directional_corretness'].tolist()
    number_of_samples = df_dir_corr_data['number_of_samples'].tolist()

    return FinalChartData(data=[BarChart(x= lookahead_days,y=directional_corretness,samples= number_of_samples,lookahead_days=lookahead_days)],
                                                start_date = str(posting_starting_date),
                                                last_updated_date = str(latest_posting_date)
                                            )

def plot_abs_delta_auto(y_variable, month, year,y_label,months_dict,y_code):
    # print("@@18")
    df_op= getting_publicposting_files_auto(y_variable, month, year,y_label,months_dict)
    df_op.rename(columns= {y_code: 'y_prediction', y_variable: 'y_shifted'},inplace=True)
    df_op = df_op.reset_index()
    # Below if statements are being used because at the 1st day of month we will not have
    # any data and the column 'Lookahead Number' is used as colour while plotting so we can't leave it empty
    
    if len(df_op) != 0:
        df_op['abs_delta'] = ((abs((df_op['y_prediction'] - df_op['y_shifted']) / df_op['y_shifted'])) * 100).round(1)
        df_op['Lookahead Number'] = [int(row[14:]) for row in df_op['lookahead_days']]

    if len(df_op) == 0:
        df_op['index'] = [int(i + 1) for i in range(30)]
        df_op['Date'] = [int(i + 1) for i in range(30)]
        df_op['y_prediction'] = [int(i + 1) for i in range(30)]
        df_op['lookahead_days'] = [int(i + 1) for i in range(30)]
        df_op['Date_of_posting'] = [int(i + 1) for i in range(30)]
        df_op['y_unshifted'] = [int(i + 1) for i in range(30)]
        df_op['y_shifted'] = [int(i + 1) for i in range(30)]
        df_op['abs_delta'] = [int(i+1) for i in range(30)]
        df_op['Lookahead Number'] = [int(i+1) for i in range(30)]

    df_op = df_op.sort_values(by=['Lookahead Number'], ascending=True)

    return df_op



def update_abs_delta(df_abs_delta, y_label, pdesk_y):
    # print("@@19")

    if pdesk_y == '3_cpo_bmd_prices_USD_per_MT':
        posting_starting_date = '24-02-2022'
    elif pdesk_y == 'basis_spot_future_bmd' or pdesk_y == 'basis_spot_future_mcx':
        posting_starting_date = '02-03-2022'
    elif pdesk_y == 'bmd_spot_price' or pdesk_y == 'mcx_spot_price' or pdesk_y == 'soyoil_ncdex_spot_price':
        posting_starting_date = '24-02-2022'
    elif pdesk_y == '2-3_soyoil_cbot_prices_USD_per_MT':
        posting_starting_date = '24-02-2022'
    else:
        posting_starting_date = 'Updating'

    date_list = []
    month_list = []
    year_list = []
    date, month, year, all_date_and_year = function_for_startandend_monthandyear(pdesk_y)
    for ele in all_date_and_year:
        date_list.append(ele[:2])
        month_list.append(ele[3:5])
        year_list.append(ele[6:])

    v = []

    for i in range(len(date_list)):
        s = str(year_list[i]) + '-' + str(month_list[i]) + '-' + str(date_list[i])
        v.append(s)
    latest_posting_date = max(v)
    # df_abs_delta.to_csv("absdelta.csv")
    # To be discuss
    df_abs_delta["abs_delta"] = df_abs_delta["abs_delta"].fillna(0)
    # x_data = df_abs_delta["Lookahead Number"].tolist()
    # y_data = df_abs_delta["abs_delta"].astype("float").tolist()
    gb_df = df_abs_delta.groupby(df_abs_delta["Lookahead Number"])
    graph_data = []
    for lookahead in df_abs_delta["Lookahead Number"].unique():
        # x_data = gb_df.get_group(lookahead)["year"].astype(str).tolist()
        y_data = gb_df.get_group(lookahead)["abs_delta"].astype(float).tolist()
        graph_data.append(BoxChart(x=[],y=y_data,name=str(lookahead)))
    

    return FinalChartData(data=graph_data,
                                    start_date = str(posting_starting_date),
                                    last_updated_date = str(latest_posting_date))

#   x: List[Any]
    # y: List[Any]
    # name: str
    # fig = px.box(df_abs_delta, x='Lookahead Number', y='abs_delta', color='Lookahead Number', labels = None, )

    # fig.update_layout(
    #     title=title[pdesk_y] + ' Absolute Delta Based on Public Posting',
    #     xaxis_title="Lookahead Days",
    #     yaxis_title="Absolute Delta as % of Actual Price",
    #     legend=dict(
    #         orientation="h",
    #         yanchor="bottom",
    #         y=0.50,
    #         xanchor="right",
    #         x=1
    #     ),
    #     showlegend=False
    #     )
    # update_fig(fig)
    # return html.Div([
    #     html.H3([
    #         ("Public Posting for {} started on {} and latest updated on {}".format(yvariable[pdesk_y], posting_starting_date, latest_posting_date)),
    #     ], style={'background': '#fff', 'color': 'black', 'height': '30px', 'font-size': '20px',
    #               'text-align': 'center'}),
    #     dcc.Graph(id="simple_abs_delta", figure=fig, config={
    #         'displaylogo': False,
    #         'displayModeBar': True,
    #         'modeBarButtonsToRemove': ['toImage']
    #     }),
    # ])


def get_dependent_values(y_variable,high_impact_cases,months_dict):
    date, month_codes, years, all_date_and_year = function_for_startandend_monthandyear(y_variable)
    months = [months_dict[str(code)] for code in month_codes]
    new_hight_impact_cases = []
    if(y_variable == "basis_spot_future_bmd" or y_variable=="basis_spot_future_mcx"):
        new_hight_impact_cases = [item for item in high_impact_cases if item not in set([3,5])]
    else:
        new_hight_impact_cases = [item for item in high_impact_cases if item not in set([10,20,30])]
        data = {
            "months" : months,
            "years" : [str(year) for year in years],
            "high_impact_cases" : new_hight_impact_cases
        }
    return data

def get_predicted_directional_correctness_graph(y_variable,y_label, month_case, year_case, high_impact_cases,months_dict,y_code):
    if (y_variable =='basis_spot_future_bmd' or y_variable== 'basis_spot_future_mcx' ) and month_case == "February":
        return
    else:
        df_dir_corr_data = plot_dir_corr_auto(y_variable, month_case, year_case, high_impact_cases,y_label,months_dict,y_code)
        return update_directional_correctness(df_dir_corr_data, y_variable, y_label, high_impact_cases)

def get_predicted_absolute_delta_graph(y_variable, month_case_abs, year_case_abs, y_label, months_dict,y_code):
    if (y_variable =='basis_spot_future_bmd' or y_variable== 'basis_spot_future_mcx' ) and month_case_abs == "February":
        return
    else:
        df_abs_delta= plot_abs_delta_auto(y_variable, month_case_abs, year_case_abs, y_label, months_dict,y_code)
        return update_abs_delta(df_abs_delta, y_label, y_variable)
