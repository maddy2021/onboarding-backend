from cProfile import label
import json
from typing import List, Union
from datetime import date


def read_json_file(json_file_path):
    json_data = {}
    with open(json_file_path,"r+") as fp:
        json_data =json.load(fp=fp)
    return json_data

# def dropDownFormatter(input_list: Union[List[str],List[int]], extra_tag="") -> List[DropDownModel]:
#     if len(input_list)>0:
#         return [DropDownModel(label=str(item)+extra_tag,value=str(item)) if extra_tag else DropDownModel(label=str(item),value=str(item)) for item in input_list]
#     return []

def today_date_key():
    today = date.today()
    return today.strftime("%d_%m_%Y")