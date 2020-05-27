import plotly
import plotly.graph_objs as go
# import unicodedata
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from matplotlib import ticker


def gen_dropdown(figure_list=None,
                 button_labels=None,
                 default_plot=0,
                 barmode='stack',
                 df=None,
                 dropdown_col=None,
                 stack_col=None,
                 id_col=None,
                 value_col=None,
                 show_all=False,
                 text_col=None,
                 annotations=None,
                 pad_r=0,
                 pad_t=-40,
                 x_loc=-.25,
                 y_loc=1,
                 cycle_colors=7,
                 **kwargs):
    """
    Function which generates:
    
    1. Automated dropdown for input figures
    2. Figure with dropdown for specified categories in input dataframe
    
    Parameters
    ----------
    
    figure_list: list
        List of plotly figures in dictionary format
        Only used if df is not provided
    
    button_labels: list, optional
        Only used if figure_list is Provided
        List of button labels assigned to dropdown
        Of not provided, trace names will be used
   
    barmode: {stack, group}, optional
        Defaults to stack 
        Only valid for traces of go.Bar() type
    
    default_plot: int, optional
        Plot to show on first visualization
        Defautlts to 0
    
    df: pd.DataFrame, optional
        Dataframe from which to derive plots
        Only used if figure_list is not provided
        
    dropdown_col: str, optional
        Must be provided if df is provided
        Contains categories to display on dropdown menu
    
    stack_col: str, optional
        Must be provided if df is provided
        Contains categories to stack on barplots
    
    id_col: str, optional
        Must be provided if df is provided
        Contains column on which to group data
        Will end up as labels on yaxis
        
    value_col: str, optional
        Must be provided if df is provided
        Will be used to provide aggrgate values for bars
        
    show_all: bool, optional
        Defaults to True
        If True, first plot will contain without dropdown filter
    
    text_col: str, optional
        Must be provided if df is provided
    
    annotations: list, optional
        Must be a list of dicts with annotation attributes
        Should not conflict with existing annotations

    pad_r: float, optional
        Right side padding for menu buttons
        Defaults to 0

    pad_t: float, optional
        Top padding for menu buttons
        Defaults to -40

    x_loc: float in interval [-2, 3], optional
        x axis location for menu buttons
        Defaults to -.25

    y_loc: float in interval [-2, 3], optional
        y axis location for menu buttons
        Defaults to 1
        
    **kwargs: optional
        Inputs to layout object
        
    Returns
    -------
        plotly.figure object
    """
    
    if figure_list:
        if df is not None:
                raise CustomError('Cannot provide both figures and dataframe!')
        
        trace_counter=0
        for figure in figure_list:
            if type(figure) != dict:
                raise TypeError('Figure object must be converted to type dict via to_plotly_json or\
                                 to_dict methods')
            data_component = figure['data']
            for trace in data_component:
                trace_counter += 1                    
        master_figure = go.Figure()
        visible_list=[False]*trace_counter
        buttons=[]
        trace_counter=0
        button_counter=0
        for figure in figure_list:
            data_component = figure['data']
            visible_list_temp = visible_list.copy()
            for trace in data_component:
                if ('visible' in trace.keys() and trace['visible'] == 'legendonly') :
                    temp_visible = 'legendonly'
                    trace['visible'] = 'legendonly' if button_counter == default_plot else False
                else:
                    temp_visible = True
                    trace['visible'] = True if button_counter == default_plot else False
                visible_list_temp[trace_counter] = temp_visible
                master_figure.add_trace(trace)
                trace_counter+=1
            buttons.append(dict(
                          args=[{'visible': visible_list_temp},
                                {key : value for key, value in zip(figure['layout'].keys(),
                                 figure['layout'].values())}],
                                 method="update",
                                 label=button_labels[button_counter] 
                                       if button_labels 
                                       else figure['layout']['title']['text']))
            button_counter+=1
            del visible_list_temp
        
        master_figure.update_layout({key:value 
                                     for key, value 
                                     in zip(figure_list[default_plot]['layout'].keys(),
                                            figure_list[default_plot]['layout'].values())},
                                      barmode=barmode,
                                      updatemenus=[
                                      dict(active=default_plot,
                                           buttons=buttons,
                                           direction="down",
                                           pad={"r": pad_r, "t": pad_t},
                                           showactive=True,
                                           x=x_loc,
                                           y=y_loc,
                                           xanchor="left",
                                           yanchor="top")],
                                           **kwargs) 
        if annotations:
            annotation_list=list(master_figure['layout']['annotations'])
            annotation_list.extend(annotations)
            master_figure.update_layout(annotations=annotation_list)
        
        return master_figure
    
    else:
        if df is not None:
            if figure_list:
                raise CustomError('Cannot provide both figures and dataframe!')
            data_list = []
            buttons=[]
            trace_counter=0
            visible_counter=0
            if show_all:
                visible_list = [False]*(df[stack_col].nunique()+
                                        df[dropdown_col].nunique()*df[stack_col].nunique())
                visible_list_temp = visible_list.copy()
                
                # Create temporary dataframe for barplots without dropdown filters
                df_temp = df.groupby([id_col,
                                               stack_col])\
                                     .agg({value_col: 'sum'})\
                                     .unstack().reset_index()

                df_temp = df_temp.reindex(df_temp[[value_col]].sum(axis=1)
                                                              .sort_values(ascending=False)
                                                              .index, axis=0)

                df_temp.columns = df_temp.columns.get_level_values(0)


                df_temp = df_temp.join((100.0*df_temp[[value_col]]
                                        .div(df_temp[[value_col]]
                                        .sum(axis=1),axis=0)
                                        .rename(columns={value_col:'{} pct'
                                                         .format(stack_col)})))

                pct_cols = list('{} pct'.format(x)
                                       for x in df[stack_col].unique())

                columns = [id_col] + list(df[stack_col].unique()) + pct_cols
                
                df_temp.columns = columns

                df_temp = df_temp[::-1]
                df_temp = df_temp.melt(id_vars=[id_col],
                                        value_vars=df[stack_col].unique(),
                                        var_name=stack_col,
                                        value_name=value_col).join(
                                                                   df_temp.melt(value_vars=pct_cols,
                                                                   value_name='Ticket %')[['Ticket %']])
                
                for cat2 in df_temp[stack_col].unique():
                    df_subset = df_temp[(df_temp[stack_col]==cat2)]
                    
                    trace = go.Bar(x=df_subset[value_col],
                                   y=df_subset[id_col],
                                   visible = True if default_plot == 0 else False,
                                   text=df_subset['Ticket %'].apply(lambda x: 
                                                                          '{}%'.format(round(x,2))) 
                                                                    if text_col else None,
                                   textposition='inside',
                                   orientation='h',
                                   name=str(cat2))
                    data_list.append(trace)
                    visible_list_temp[trace_counter] = True
                    trace_counter +=1
                del df_temp
                del df_subset
                visible_counter +=1
                buttons.append(dict(
                                args=[{'visible': visible_list_temp}],
                                      method="update",
                                      label='All'))
                del visible_list_temp
                for cat1 in df[dropdown_col].unique(): 
                    visible_list_temp = visible_list.copy()
                    for cat2 in df[stack_col].unique():
                        df_deep_subset = df[(df[dropdown_col]==cat1) & 
                                            (df[stack_col]==cat2)]

                        trace = go.Bar(x=df_deep_subset[value_col],
                                       y=df_deep_subset[id_col],
                                       visible = True if visible_counter == default_plot else False,
                                       text=df_deep_subset[text_col].apply(lambda x: 
                                                                          '{}%'.format(round(x,2)))
                                                                           if text_col else None,
                                       textposition='inside',
                                       orientation='h',
                                       name=str(cat2))
                        data_list.append(trace)
                        visible_list_temp[trace_counter] = True
                        trace_counter += 1
                    buttons.append(dict(
                    args=[{'visible': visible_list_temp}],
                          method="update",
                          label=str(cat1)))
                    del visible_list_temp
                    del df_deep_subset
                    visible_counter+=1
            else:
                visible_list = [False]*(df[dropdown_col].nunique()*df[stack_col].nunique())
                visible_counter = 0
                for cat1 in df[dropdown_col].unique(): 
                    visible_list_temp = visible_list.copy()
                    for cat2 in df[stack_col].unique():
                        df_deep_subset = df[(df[dropdown_col]==cat1) & 
                                            (df[stack_col]==cat2)]

                        trace = go.Bar(x=df_deep_subset[value_col],
                                       y=df_deep_subset[id_col],
                                       visible = True if visible_counter == default_plot else False,
                                       text=df_deep_subset[text_col].apply(lambda x: 
                                                                          '{}%'.format(round(x,2)))
                                                                           if text_col else None,
                                       textposition='inside',
                                       orientation='h',
                                       name=str(cat2))
                        data_list.append(trace)
                        visible_list_temp[trace_counter] = True
                        trace_counter += 1
                    buttons.append(dict(
                    args=[{'visible': visible_list_temp}],
                          method="update",
                          label=str(cat1)))
                    visible_counter+=1
                    del visible_list_temp
                    del df_deep_subset
                    
            master_figure = go.Figure(data=data_list)
            master_figure.update_layout(barmode=barmode,
                                        xaxis=dict(automargin=True),
                                        yaxis=dict(automargin=True),
                                        legend=dict(traceorder='normal'),
                                        annotations=annotations,
                                        updatemenus=[dict(active=default_plot,
                                                          buttons=buttons,
                                                          direction="down",
                                                          pad={"r": pad_r, "t": pad_t},
                                                          showactive=True,
                                                          x=x_loc,
                                                          y=y_loc,
                                                          xanchor="left",
                                                          yanchor="top")],
                                         **kwargs)
            if float(re.search('^[^\.]*\.[^\.]*', plotly.__version__).group(0)) >= 4.2:
                master_figure.update_layout(uniformtext=dict(minsize=6,
                                                             mode='hide'))

            return master_figure
    

def plot_rt(name, result, ax, c=(.3,.3,.3,1), ci=(0,0,0,.05)):
    ax.set_ylim(0.5, 1.6)
    ax.set_title(name)
    ax.plot(result['median'],
            marker='o',
            markersize=4,
            markerfacecolor='w',
            lw=1,
            c=c,
            markevery=2)
    ax.fill_between(
        result.index,
        result['lower_90'].values,
        result['upper_90'].values,
        color=ci,
        lw=0)
    ax.axhline(1.0, linestyle=':', lw=1)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
