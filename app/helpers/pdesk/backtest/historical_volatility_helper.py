import pandas as pd
from app.core.config import settings
from app.schemas.pdesk import FinalChartData, ScatterChart


def create_graph_data(y_variable,label_name,operation,updated_date):
    df_final = pd.read_csv(settings.DATA_FILE_PATH+"/Pdesk/edibleoil_volatility/{}.csv".format(label_name))
    graph_data = []
    gp_df = df_final.groupby(df_final["Year"])
    
    for year in df_final["Year"].unique():
        x_data = gp_df.get_group(year)["Timeframe(Days)"].tolist()
        y_data = gp_df.get_group(year)["Volatility(Perc_Change%) - {}".format(operation)].tolist()
        graph_data.append(ScatterChart(x=x_data,y=y_data,year=str(year)))
    final_graph_data = FinalChartData(data=graph_data,last_updated_date=updated_date)
    return final_graph_data
