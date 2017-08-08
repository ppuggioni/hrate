import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from os.path import isfile, join
from os import listdir
from collections import OrderedDict
from hrate.data_handling.selfloops import read_selfloops_file
import logging

FORMAT = '%(asctime)-15s  %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

app = dash.Dash()

# LOADING data
DATADIR = 'data/selfloops'
file_paths = [join(DATADIR, f) for f in listdir(DATADIR) if isfile(join(DATADIR, f)) if f.endswith('.txt')]

data = OrderedDict()
for f in file_paths:
    data[f.split('/')[-1]] = read_selfloops_file(f)

available_files = list(data.keys())

app.layout = html.Div([

    html.H4('Select File'),

    html.Div([
        dcc.Dropdown(
            id='file_name',
            options=[{'label': i, 'value': i} for i in available_files],
            value=available_files[0]
        )
    ]),

    html.H3('Heart Rate'),
    dcc.Markdown(
        '''
        - To zoom in, simply use your mouse
        - To visualise RR intervals in the bottom plot, use the __Box Select__ option.
        - The light pink area is the selected one, and on the histogram you see the HR distribution in that range
        - The grey area is the one which is visualised in the bottom plot. It is restricted to 5 minutes due to rendering problems.
        '''
    ),

    html.Div([
        html.Div([dcc.Graph(id='HR_plot')], style={'width': '60%', 'display': 'inline-block', 'padding': '0 20'}),
        html.Div([dcc.Graph(id='HR_summary')], style={'width': '35%', 'display': 'inline-block', 'padding': '20 0'}),
    ]),

    html.H4('Beat-by-beat Data'),
    html.Div(
        [
            html.Div([dcc.Graph(id='RR_plot')], style={'width': '60%', 'display': 'inline-block', 'padding': '0'}),
            html.H4('Summary RR events', style={'width': '35%', 'padding': '0'}),
            html.Div([html.Pre(id='RR_summary')], style={'width': '35%', 'padding': '0'}),
        ]
    ),

    html.Div(
        [
            html.H4('Summary HR events', style={'width': '35%', 'padding': '0'}),
            html.Div([html.Pre(id='HR_summary_stats')], style={'width': '35%', 'padding': '0'}),
        ]
    )

])


@app.callback(
    dash.dependencies.Output('HR_plot', 'figure'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('RR_plot', 'figure'),
     dash.dependencies.Input('HR_plot', 'selectedData')])
def update_HR_graph(file_name, rr_plot, hr_selected_data):
    dff = data[file_name]

    # get range of RR, to be drawn here
    plot_data = []

    if hr_selected_data is not None:
        x_stamp_min = pd.to_datetime(hr_selected_data['range']['x'][0])
        x_stamp_max = pd.to_datetime(hr_selected_data['range']['x'][1])
        y_max = dff['HR'].max()

        RR_range_plot = go.Scatter(
            x=[x_stamp_min, x_stamp_max],
            y=[y_max, y_max],
            fill='tozeroy',
            mode='lines',
            line=dict(
                color='#EB89B5',
            ),
            showlegend=False,
        )
        plot_data.append(RR_range_plot)

    if 'range' in rr_plot['layout']['xaxis'].keys():
        RR_plot_range = rr_plot['layout']['xaxis']['range']
        y_max = dff['HR'].max()
        y_min = dff['HR'].min()

        RR_range_plot = go.Scatter(
            x=RR_plot_range,
            y=[y_max, y_max],
            fill='tozeroy',
            mode='lines',
            line=dict(
                color='rgb(80, 80, 80)',
            ),
            showlegend=False,
        )
        plot_data.append(RR_range_plot)

    dff = resample_df(dff)

    HR_data = go.Scatter(
        x=dff['Time_stamp'],
        y=dff['HR'],
        mode='lines+markers',
        line={
            'color': ('rgb(205, 12, 24)'),
            'width': 2
        },
        marker={
            'size': 4
        },
        showlegend=False
    )
    plot_data.append(HR_data)

    figure_hr_plot = {
        'data': plot_data,
        'layout': go.Layout(
            xaxis={
                "rangeselector": {
                    "buttons": [
                        {
                            "count": 5,
                            "step": "minute",
                            "stepmode": "backward",
                            "label": "5m"
                        },
                        {
                            "count": 30,
                            "step": "minute",
                            "stepmode": "backward",
                            "label": "30m"
                        },
                        {
                            "count": 1,
                            "step": "hour",
                            "stepmode": "backward",
                            "label": "1h"
                        },
                        {
                            "count": 4,
                            "step": "hour",
                            "stepmode": "backward",
                            "label": "4h"
                        },
                        {
                            "step": "all"
                        }
                    ]
                },
                "rangeslider": {},
                "type": "date"
            },
            yaxis={
                'title': 'Heart Rate (bpm)',
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest'
        )}

    return figure_hr_plot


@app.callback(
    dash.dependencies.Output('HR_summary', 'figure'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('HR_plot', 'selectedData'),
     ])
def update_hr_summary_figure(file_name, HR_plot_selected):
    # TODO: do create and update!
    # TODO: histogram is wrong, it needs to have resampled uniform data on the x-axis!!
    dff = data[file_name]

    plot_data = [go.Histogram(
        y=dff['HR'].values,
        marker=dict(
            color=('rgb(205, 12, 24)')
        ),
        histnorm='probability',
        name='All data',
        opacity=0.4
    )]
    # TODO: bug! this is called rarely and does not work, because the range is not the xaxis lim!!!
    if HR_plot_selected is not None:
        x_stamp_min = pd.to_datetime(HR_plot_selected['range']['x'][0])
        x_stamp_max = pd.to_datetime(HR_plot_selected['range']['x'][1])

        idx = (data[file_name]['Time_stamp'] > x_stamp_min) & \
              (data[file_name]['Time_stamp'] < x_stamp_max)
        dff_select = data[file_name].loc[idx]

        plot_selected_data = go.Histogram(
            y=dff_select['HR'].values,
            marker=dict(
                color='#EB89B5'
            ),
            histnorm='probability',
            name='Selected range',
            opacity=0.6
        )
        plot_data.append(plot_selected_data)

    return {'data': plot_data,
            'layout': go.Layout(
                title='HR (bpm)',
                barmode='overlay',
                legend=dict(x=0.9, y=0.9)
            )
            }


@app.callback(
    dash.dependencies.Output('RR_plot', 'figure'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('HR_plot', 'selectedData'),
     ])
def update_RR_graph(file_name, x_selected_hr):
    if x_selected_hr is None:
        dff = data[file_name].head(0)
    else:
        x_stamp_min = pd.to_datetime(x_selected_hr['range']['x'][0])
        x_stamp_max = pd.to_datetime(x_selected_hr['range']['x'][1])

        x_stamp_max = min(x_stamp_min + pd.to_timedelta(300, unit='s'), x_stamp_max)

        idx = (data[file_name]['Time_stamp'] > x_stamp_min) & \
              (data[file_name]['Time_stamp'] < x_stamp_max)
        dff = data[file_name].loc[idx]

    RR_data = go.Scatter(
        x=dff['Time_stamp'],
        y=dff['RR'],
        text=dff['HR'],
        mode='lines+markers',
        marker={
            'size': 5,
            'opacity': 1,
            'color': ('rgb(22, 96, 167)'),
            'line': {'width': 0.5, 'color': 'white'}
        },
        line={
            'color': ('rgb(30, 30, 30)'),
            'width': 0.3,
        }
    )

    return {
        'data': [RR_data],
        'layout': go.Layout(
            xaxis={
                "rangeselector": {
                    "buttons": [
                        {
                            "count": 5,
                            "step": "minute",
                            "stepmode": "backward",
                            "label": "5m"
                        },
                        {
                            "count": 10,
                            "step": "minute",
                            "stepmode": "backward",
                            "label": "10m"
                        },
                        {
                            "step": "all"
                        }
                    ]
                },
                "rangeslider": {},
                "type": "date"
            },
            yaxis={
                'title': 'RR intervals (ms)',
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }


@app.callback(
    dash.dependencies.Output('RR_summary', 'children'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('HR_plot', 'selectedData'),
     ])
def create_RR_summary(file_name, x_selected_hr):
    # TODO: create a list of the slowest and fastest. Make it click and highlight the intervals on the RR plot
    max_RR_idx = data[file_name]['RR'].idxmax()
    min_RR_idx = data[file_name]['RR'].idxmin()

    out = "Min. interval = {} ms at {} \n" \
          "Max. interval = {} ms at {} \n".format(data[file_name].loc[min_RR_idx,'RR'],
                                                  data[file_name].loc[min_RR_idx, 'Time_stamp'],
                                                  data[file_name].loc[max_RR_idx, 'RR'],
                                                  data[file_name].loc[max_RR_idx, 'Time_stamp'],
                                                  )



    if x_selected_hr is not None:
        x_stamp_min = pd.to_datetime(x_selected_hr['range']['x'][0])
        x_stamp_max = pd.to_datetime(x_selected_hr['range']['x'][1])

        x_stamp_max = min(x_stamp_min + pd.to_timedelta(300, unit='s'), x_stamp_max)

        idx = (data[file_name]['Time_stamp'] > x_stamp_min) & \
              (data[file_name]['Time_stamp'] < x_stamp_max)

        selection_max_RR =  data[file_name].loc[idx, 'RR'].idxmax()
        selection_min_RR = data[file_name].loc[idx, 'RR'].idxmin()
        out += '\n Selected Range:\n'
        out2 = "Min. interval = {} ms at {} \n" \
               "Max. interval = {} ms at {} \n".format(data[file_name].loc[selection_min_RR, 'RR'],
                                                      data[file_name].loc[selection_min_RR, 'Time_stamp'],
                                                      data[file_name].loc[selection_max_RR, 'RR'],
                                                      data[file_name].loc[selection_max_RR, 'Time_stamp'],
                                                      )

        out += out2


    return out


@app.callback(
    dash.dependencies.Output('HR_summary_stats', 'children'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('HR_plot', 'selectedData'),
     ])
def create_HR_summary(file_name, x_selected_hr):
    # TODO: create a list of the slowest and fastest. Make it click and highlight the intervals on the RR plot
    max_HR_idx = data[file_name]['HR'].idxmax()
    min_HR_idx = data[file_name]['HR'].idxmin()

    out = "Min. HR = {}/min at {} \n" \
          "Max. HR = {}/min at {} \n".format(data[file_name].loc[min_HR_idx,'HR'],
                                                  data[file_name].loc[min_HR_idx, 'Time_stamp'],
                                                  data[file_name].loc[max_HR_idx, 'HR'],
                                                  data[file_name].loc[max_HR_idx, 'Time_stamp'],
                                                  )

    return out

def resample_df(df):
    if len(df.index) < 1000:
        return df

    step = int(len(df.index) / 1000)
    idx_keep = np.arange(0, len(df.index), step)
    return df.loc[idx_keep]


if __name__ == '__main__':
    app.config.supress_callback_exceptions = True
    app.run_server()
