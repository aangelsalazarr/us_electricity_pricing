import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

################################################################
## GENERAL DATA TRANSFORM FUNCTIONS
################################################################
def combine_csv_files(csv_path: str):
    '''
    Args: provide path of directory containing a bunch of csv files

    Output: return master df
    '''

    csv_files = glob.glob(os.path.join(csv_path, "*.csv"))
 
    dfs = []
    
    for file in csv_files:
        df = pl.read_csv(file)
        dfs.append(df)
    
    master_df = pl.concat(dfs)
    
    return master_df


def create_std_timestamp(dataframes: list, cols_keep: list):
    '''
    Given a dataframe, convert timestamp to formmatted time stamp

    cols to keep default:
    ['node_id', 'timestamp', '5min_lmp', "iso_id"]
    '''
    df_filtered = [dataset.select(cols_keep) for dataset in dataframes]

    # here is where we will be adding our new dfs
    new_dfs = []

    # iterate through each df, and create a 'formatted_timestap' column that only includes Hour and Minute
    for df in df_filtered:
        temp_df = df.with_columns(
            pl.col('timestamp').dt.strftime("%m-%d-%Y %H:%M").alias('fmt_timestamp')
            )
        
        temp_df = temp_df.with_columns(
            pl.col("fmt_timestamp").str.strptime(pl.Datetime, format="%m-%d-%Y %H:%M")
        )

        new_dfs.append(temp_df)

    # removing timezone from columns with UTC timezone def
    new_dfs = [df.with_columns(
        pl.col("timestamp").dt.replace_time_zone(None), 
        pl.col('fmt_timestamp').dt.replace_time_zone(None)
    ) for df in new_dfs]

    combined_dfs = pl.concat(new_dfs, how="vertical")
    
    # converting into pandas df so it works with seaborn
    combined_pandas_df = combined_dfs.to_pandas()

    return combined_pandas_df


def plot_lmp(dataframe: object, col_choose:str, geo_dataframe:object):
    '''
    Given a dataframe, plot it on the map to show lmp stats summaries
    '''
    # insert explanation here
    master_geom = [Point(xy) for xy in zip(dataframe['longitude'], dataframe['latitude'])]

    master_gdf = gpd.GeoDataFrame(dataframe, geometry=master_geom, 
                                        crs='EPSG:4326')  # WG84

    master_web = master_gdf.to_crs(epsg=3857)
    ##master_web.info()
    master_web = master_web.reset_index(drop=True)
    ## master_web.plot(markersize=1)

    geo_dataframe = geo_dataframe.to_crs(master_web.crs)
    fig, axis = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor('#fffff2') 

    master_web.plot(markersize=5, column=col_choose, cmap='seismic', 
                    legend=True, ax=axis)
    geo_dataframe.plot(facecolor='none', edgecolor='#475569', ax=axis, alpha=1)

    plt.title('USA Locational Marginal Pricing $/MWh\n' + 
            f"{master_web['formatted_timestamp'][0]}")

    plt.tight_layout()
    plt.axis("off")
    plt.show()


def tier_lmps(dataframe: object):
    '''
    Args
    Dataframe

    Output
    Creates new column called "price_tier" to show where price lies in distribution
    '''

    bins = [-20, -10, 0, 10, 25, 50, 75, 100, 150, 200, 225]
    labels = ['<-40','-20', '-10', '0', '10', '25', '50', '75', '100', '150','200', '>225']

    dataframe = dataframe.with_columns(
        pl.col("5min_lmp").cut(breaks=bins, labels=labels).alias("5min_price_type"),)

    return dataframe


################################################################
## ERCOT TRANSFORM DATA
################################################################
def transform_ercot_data(ercot_df: object):
    '''
    given ercot df or file, return a transformed verion
    changes scedtimestamp to datetime type...
    '''

    ercot_df = ercot_df.rename(
        {"LMP": "5min_lmp",
         "settlementPoint": "node_id",
         "SCEDTimestamp": "timestamp"
         })
    
    # removing the seconds of ERCOT time stamp, causing issues....
    ercot_df = ercot_df.with_columns(
        pl.col("timestamp").str.replace(r'..$', "00")
    )
    
    ercot_df = ercot_df.with_columns(
        pl.col("timestamp").str.strptime(pl.Datetime, format="%Y-%m-%dT%H:%M:%S")
    )

    ercot_df = ercot_df.with_columns(
        pl.lit("ERCOT").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'), 
        pl.col('timestamp').dt.minute().alias('minute')
    )

    return ercot_df


################################################################
## CAISO TRANSFORM DATA
################################################################
def transform_caiso_data(caiso_df: object):
    '''
    Given a caiso object make necessary adjustments to standardize the dataset
    '''
    caiso_df = caiso_df.rename(
        {"RESOURCE_NAME": "node_id",
         "VALUE": "5min_lmp"}
    )

    caiso_df = caiso_df.with_columns(
        pl.col("INTERVAL_START_GMT")
        .str.to_datetime(format="%Y-%m-%d %H:%M:%S%:z")
        .dt.convert_time_zone("UTC"),
        pl.col("INTERVAL_END_GMT")
        .str.to_datetime(format="%Y-%m-%d %H:%M:%S%:z")
        .dt.convert_time_zone("UTC")
    )

    caiso_df = caiso_df.rename(
        {"INTERVAL_END_GMT": "timestamp"}
    )

    caiso_df = caiso_df.with_columns(
        pl.lit("CAISO").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return caiso_df


################################################################
## NYISO TRANSFORM DATA
################################################################
def transform_nyiso_data(nyiso_df:object):
    '''
    Given nyiso df, standardize dataset and return
    '''
    nyiso_df = nyiso_df.rename(
        {"Time Stamp": "timestamp",
         "LBMP ($/MWHr)": "5min_lmp", 
         "Name": "node_id"}
    )
    nyiso_df = nyiso_df.with_columns(
        pl.col("timestamp").str.strptime(pl.Datetime, 
                                         format="%m/%d/%Y %H:%M:%S")
    )

    nyiso_df = nyiso_df.with_columns(
        pl.lit("NYISO").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return nyiso_df


################################################################
## SPP TRANSFORM DATA
################################################################
def transform_spp_data(spp_df:object):
    '''
    Given nyiso df, standardize dataset and return
    '''
    spp_df = spp_df.rename(
        {"GMTIntervalEnd": "timestamp",
         "LMP": "5min_lmp", 
         "Settlement Location": "node_id"}
    )
    spp_df = spp_df.with_columns(
        pl.col("timestamp").str.strptime(pl.Datetime, 
                                         format="%m/%d/%Y %H:%M:%S")
    )

    spp_df = spp_df.with_columns(
        pl.lit("SPP").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return spp_df


################################################################
## ISONE TRANSFORM DATA
################################################################
def transform_isone_data(isone_df:object):
    '''
    Given nyiso df, standardize dataset and return
    '''
    isone_df = isone_df.rename(
        {"BeginDate": "timestamp",
         "LmpTotal": "5min_lmp", 
         "LocationName": "node_id"}
    )

    # 2025-05-17T17:00:00.000-04:00  <-- what the timestamp looks like
    isone_df = isone_df.with_columns(
        pl.col("timestamp").str.strptime(pl.Datetime, format=None)
    )

    isone_df = isone_df.with_columns(
        pl.lit("ISONE").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return isone_df


################################################################
## PJM TRANSFORM DATA
################################################################
def transform_pjm_data(pjm_df:object):
    '''
    Given nyiso df, standardize dataset and return
    '''
    pjm_df = pjm_df.rename(
        {"datetime_beginning_utc": "timestamp",
         "total_lmp_rt": "5min_lmp", 
         ## "hourly_lmp": "1hr_lmp",
         "pnode_name": "node_id"}
    )
    pjm_df = pjm_df.with_columns(
        pl.col("timestamp").str.to_datetime("%Y-%m-%dT%H:%M:%S")
    )

    pjm_df = pjm_df.with_columns(
        pl.lit("PJM").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return pjm_df

################################################################
## MISO TRANSFORM DATA
################################################################
def transform_miso_data(miso_df:object):
    '''
    Given nyiso df, standardize dataset and return
    '''
    miso_df = miso_df.rename(
        {"end_time": "timestamp",
         "lmp": "5min_lmp", 
         "node": "node_id"}
    )
    miso_df = miso_df.with_columns(
        pl.col("timestamp").str.to_datetime("%Y-%m-%dT%H:%M:%S%.f")
    )

    miso_df = miso_df.with_columns(
        pl.lit("MISO").alias("iso_id"),
        pl.col('timestamp').dt.hour().alias('hour'),
        pl.col('timestamp').dt.minute().alias('minute')

    )

    return miso_df