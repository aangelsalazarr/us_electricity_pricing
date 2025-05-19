# purpose is to centralize process of pulling lmp data
from private_info import ercot_functions as efuncs
from private_info import credentials as creds  # this stores ISO creds
from private_info import ercot_api_struct as eas # stores api structure framework

# now we are loading info from spp pull function in
from private_info import spp_functions as sfuncs

# now we are loading in from nyiso pull function
from private_info import nyiso_functions as nfuncs

# loading in from caiso pull function
from private_info import caiso_functions as cfuncs
from private_info import caiso_api_struct as cas

# loading in from isone pull function 
from private_info import isone_functions as ifuncs
import polars as pl


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
    topic_id=eas.lmp_by_node['topic_id'], 
    choose_date=None
)

# initializing the class for ercot
ercot_client.get_lmp_data()


# setting up SPP function pull
sfuncs.pull_spp_lmp(choose_date="20250517", topic_id='LMP_By_SETTLEMENT_LOC', file_type='csv', 
            save_path="datasets/spp_lmp_data")


# setting up NYISO function pull
nfuncs.grab_nyiso_daily_lbmp(date_pull="20250517", save_path="datasets/nyiso_lmp_data", 
                      topic_id="realtime_zone")


# setting up ISONE function pull
# need to first load in our csv file with hubs/node ids
local_isone_hubs = pl.read_csv('private_info/isone_lmp_locations.csv')
ifuncs.aggregate_isone_lmps(locations=local_isone_hubs, begin_date=f"20250517",
                     auth_uname=creds.isone_creds['username'], 
                     auth_pword=creds.isone_creds['password'], 
                     topic_id="fiveminutelmp",
                     save_path="datasets/isone_lmp_data"
                                     )


# setting up function to pull from caiso as well
caiso_client = cfuncs.CAISO_LMP_Client(
    topic_id=cas.fivemin_lmp['topic_id'], 
    choose_date='20250517', 
    save_folder='datasets/caiso_lmp_data/lmp_data_zip', 
    xml_dest='datasets/caiso_lmp_data/lmp_data_xml', 
    save_path='datasets/caiso_lmp_data', 
    csv_path='datasets/caiso_lmp_data/lmp_csv'
)

caiso_client.get_lmp_data()
