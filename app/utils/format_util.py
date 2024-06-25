from datetime import datetime


def convert_to_yyyymmdd(date_str):
    date_obj = datetime.strptime(date_str, '%d-%m-%Y')
    yyyymmdd_str = date_obj.strftime('%Y%m%d')
    return yyyymmdd_str
