import pandas as pd
import sqlalchemy
from sqlalchemy.orm import Session
# from app.db.session import SessionLocal_1


def get_data_single_filter(table_name="", column_name=""):
    if(table_name):
        # database: Session = SessionLocal_1()
        try:
            query_string = "SELECT * FROM " + table_name
            result = database.execute(sqlalchemy.text("{} WHERE pipeline_name = :column_name".format(query_string)),
                                    { 'column_name': column_name}).fetchall()
            return result
        except Exception as e:
            # Do something
            print(e)
        finally:    
            database.close()
    return ""


def getactivecontractsoyoil(tablename):
    # database: Session = SessionLocal_1()
    try:
        table_data = database.execute('SELECT * FROM {} ORDER BY "Date" DESC LIMIT 1'.format(tablename)).fetchall()
        tmp_data = database.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '{}';".format(tablename))
        database.close()
        cl_list = []
        for i in tmp_data:
            cl_list.append(i[0])
        df_daily = pd.DataFrame(table_data, columns=cl_list)
        del df_daily['index']
        #print(df_daily.iloc[-1, :]["2_soyoil_cbot_prices_USD_per_MT"])
        #print(type(df_daily.iloc[-1, :]["2_soyoil_cbot_prices_USD_per_MT"]))
        is_3_month_active = df_daily.iloc[-1, :]["2_soyoil_cbot_prices_USD_per_MT"] is None
        #print(df_daily)
        return is_3_month_active
    except Exception as e:
        # Do something
        print(e)
    finally:
        database.close()


def get_table_data(tablename):
    database: Session = SessionLocal_1()
    try:
        tmp_data = database.execute("SELECT * FROM {}".format(tablename)).fetchall()
        database.close()
        return tmp_data
    except Exception as e:
        #  Do something here
        print(e)
    finally:
        database.close()


def get_table_columns(tablename):
    database: Session = SessionLocal_1()
    try:
        tmp_data = database.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '{}';".format(tablename)).fetchall()
        database.close()
        cl_list = []
        for item in tmp_data:
            cl_list.append(item[0])
        return cl_list
    except Exception as e:
        #  Do something here
        print(e)
    finally:
        database.close()


def get_data_from_query(query):
    database: Session = SessionLocal_1()
    try:
        tmp_data = database.execute(query)
        database.close()
        return tmp_data
    except Exception as e:
        #  Do something here
        print(e)
    finally:
        database.close()
