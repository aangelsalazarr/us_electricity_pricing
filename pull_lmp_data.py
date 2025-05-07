# purpose is to centralize process of pulling lmp data
from private_info import ercot_functions as efuncs
from private_info import credentials as creds  # this stores ISO creds
from private_info import ercot_api_struct as eas # stores api structure framework

# let's set up a way to define what date dataset we want to pulll from 
from datetime import date, datetime, timedelta
set_tdelta=0
today = datetime.today()
day_num = today.strftime("%d")
month_num = today.strftime("%m")
year_num = today.strftime("%Y")


# setting up process of grabbing ercot real time LMP by node (5 minute intervals)
# we must initialize our ercot client class
ercot_client = efuncs.ERCOT_LMP_Client(
    username=creds.ercot_creds['username'], 
    password=creds.ercot_creds['password'],
    subscription_key=creds.ercot_creds['api_key'], 
    emil_id=eas.lmp_by_node['emil_id'], 
    time_from_id=eas.lmp_by_node['time_start_id'], 
    time_to_id=eas.lmp_by_node['time_end_id'], 
    topic_id=eas.lmp_by_node['topic_id']
)

# initializing the class
ercot_lmp_ercot=ercot_client.get_lmp_data()