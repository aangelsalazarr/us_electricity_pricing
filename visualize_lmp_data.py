import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import polars as pl


###############################################################################
### USED TO VISUALIZE MASTER DATA SETS
###############################################################################
def lmp_iso_fgrid(dataset: object, fgrid_type = "standard"):
    '''
    Given a master dataset containing all LMP data by 7 ISOs, return a facet grid by ISO

    fgrid_type = standard (by iso), hour_iso (by hour with iso hue)
    '''

    if fgrid_type == "standard":
        plt.figure(figsize=[24,10])

        # creating facet grid with multiple plots based on iso_id
        g = sns.FacetGrid(data=dataset,  col='iso_id', col_wrap=4)

        # mapping scatter plot to each of the grid in the facet grid
        g.map(sns.scatterplot, 'fmt_timestamp', '5min_lmp', s=10)

        # rotating x axis labels by 90 degrees
        for ax in g.axes.flat:
            ax.tick_params(axis='x', rotation=90)

        g.set_axis_labels('', 'Locational Marginal Price (LMP, $/MWh)')
        g.fig.suptitle('USA Locational Marginal Pricing ($/MWh)', fontsize=12, y=1.03)

        plt.show()


    elif fgrid_type == "hour_iso":

        plt.figure(figsize=[24,10])

        # creating facet grid with multiple plots based on iso_id
        g = sns.FacetGrid(data=dataset,  col='hour', col_wrap=6, hue='iso_id')

        # mapping scatter plot to each of the grid in the facet grid
        g.map(sns.scatterplot, 'minute', '5min_lmp', s=10)

        g.add_legend()

        # rotating x axis labels by 90 degrees
        for ax in g.axes.flat:
            ax.tick_params(axis='x', rotation=90)

        g.set_axis_labels('', 'Locational Marginal Price (LMP, $/MWh)')
        g.fig.suptitle('USA Locational Marginal Pricing ($/MWh)', fontsize=12, y=1.03)

        plt.show()

    else: 
        print('please select one of the 2 presets!')



def lmp_plot_distribution(dataset: object, vis_type = 'standard'):
    '''
    Purpose is to generate visuals associated with understanding distribution of data
    Options: standard (kde plot by iso_id), hour_iso (kde plot by hour and iso hue)
    '''
    if vis_type == "standard":
        # lets plot distribution of pricing
        plt.figure(figsize=[12,6])

        bins=range(-50, 170, 2) # low, high and seperate by N values

        g = sns.FacetGrid(data=dataset, col='iso_id', col_wrap=4)
        g.map(sns.kdeplot, '5min_lmp', clip=(-25, 100))  # clipping data range from -250 to 250 $/mwh
        g.add_legend()

        for ax in g.axes.flat:
            ax.tick_params(axis='x', rotation=90)

        g.set_axis_labels('Locational Marginal Pricing, $/MWh', 'Density')
        g.fig.suptitle('USA Locational Marginal Pricing ($/MWh)', fontsize=12, y=1.03)

        plt.grid(False)
        plt.figure()

    elif vis_type == "hour_iso":
        # lets plot distribution of pricing
        plt.figure(figsize=[12,6])

        bins=range(-50, 170, 2) # low, high and seperate by N values

        g = sns.FacetGrid(data=dataset, col='hour', col_wrap=6, hue='iso_id')
        g.map(sns.kdeplot, '5min_lmp', clip=(-25, 100))  # clipping data range from -250 to 250 $/mwh
        g.add_legend()

        for ax in g.axes.flat:
            ax.tick_params(axis='x', rotation=90)

        g.set_axis_labels('Locational Marginal Pricing, $/MWh', 'Density')
        g.fig.suptitle('USA Locational Marginal Pricing ($/MWh)', fontsize=12, y=1.03)

        plt.grid(False)
        plt.figure()

    else: 
        print('please choose a valid kde plot type!')


###############################################################################
### USED TO VISUALIZE ERCOT DATASET
###############################################################################

def lmp_node_hour_hmap(dataframe: object, plot_title: None):
    '''
    Args
        provide a dataframe in polars format and it will make transformations

    Output
        provides user with necessary objects needed to visualize correlations

    Needed: nodenames as node_id, hour values as hour and 5min lmps as 5min_lmp
    provide a title for the plot
    '''
    # group by node_id and hour then calculate mean of lmp values
    pandas_df = dataframe.to_pandas()

    pivot_df = pd.pivot_table(
        pandas_df, values='5min_lmp', index='node_id', columns='hour', aggfunc='mean'
    )

    plt.figure(figsize=[12,4])

    ax = sns.heatmap(pivot_df, cmap='coolwarm', fmt='.0f',
                    annot=True, linewidths=0.5)
    
    plt.title(f'{plot_title}')

    plt.show()

    return pivot_df



def lmp_corr_matrix(dataframe: object, index=None, columns=None):
    '''
    Returns a correlation matrix
    '''
    pandas_df = dataframe.to_pandas()

    # create pivot table with timestamps as rows and nodes as columns

    if index == None or columns == None:
        node_pivot = pd.pivot_table(
            data=pandas_df, values='5min_lmp', index='hour', columns='node_id', 
            aggfunc='mean'
        )

    else: 
        node_pivot = pd.pivot_table(
            data=pandas_df, values='5min_lmp', index=f'{index}', columns=f'{columns}', 
            aggfunc='mean'
        )
        
    # correlation matrix
    corr_matrix = node_pivot.corr()

    plt.figure(figsize=[20, 4])

    sns.heatmap(data=corr_matrix, annot=False, cmap='rocket', square=True, 
                linewidth=0.5, vmin=0.75, vmax=1)
    
    plt.title('ERCOT Hub Correlation Matrix')
    
    plt.show()

    return corr_matrix


def create_lag_plot(dataframe: object, lag_by:int, selected_node:str):
    '''
    Given a dataframe and input params, generate a lag plot
    '''
    sorted_df = dataframe.sort(['node_id', 'timestamp'])
    df_with_lag = sorted_df.with_columns(
        pl.col('5min_lmp').shift(lag_by).over('node_id').alias(f'5min_lmp_lag{lag_by}')
    )
    df_lag_clean = df_with_lag.drop_nulls(subset=[f'5min_lmp_lag{lag_by}'])
    df_node = df_lag_clean.filter(
        pl.col('node_id') == selected_node
    )
    df_pandas = df_node.select(['5min_lmp', f'5min_lmp_lag{lag_by}']).to_pandas()

    plt.figure(figsize=[8,6])
    sns.scatterplot(data=df_pandas, x='5min_lmp', y=f'5min_lmp_lag{lag_by}', alpha=0.5)

    plt.title(f'Lag Plot for {selected_node}')
    plt.grid(True)
    plt.show()