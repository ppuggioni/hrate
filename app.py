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

app = dash.Dash()

# LOADING data
DATADIR = 'data/sample/selfloops'
file_paths = [join(DATADIR, f) for f in listdir(DATADIR) if isfile(join(DATADIR, f))]

data = OrderedDict()
for f in file_paths:
    data[f.split('/')[-1]] = read_selfloops_file(f)

available_files = list(data.keys())

app.layout = html.Div([

    html.Div([
        dcc.Dropdown(
            id='file_name',
            options=[{'label': i, 'value': i} for i in available_files],
            value=available_files[0]
        )
    ]),

    html.Div([dcc.Graph(id='HR_plot')], style={'width': '60%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([dcc.Graph(id='HR_summary')], style={'width': '25%', 'display': 'inline-block'}),

    dcc.Graph(id='RR_plot')

])


@app.callback(
    dash.dependencies.Output('HR_plot', 'figure'),
    [dash.dependencies.Input('file_name', 'value'),
     dash.dependencies.Input('RR_plot', 'figure')])
def update_HR_graph(file_name, rr_plot):
    dff = data[file_name]

    # get range of RR, to be drawn here
    plot_data = []
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
     dash.dependencies.Input('HR_plot', 'figure'),
     ])
def update_hr_summary_figure(file_name, HR_plot_figure):
    # TODO: do create and update!
    # TODO: histogram is wrong, it needs to have resampled uniform data on the x-axis!!
    dff = data[file_name]

    plot_data = [go.Histogram(
        y = dff['HR'].values,
        marker=dict(
            color='#EB89B5'
        ),
        histnorm='probability',
        name='All data',
        opacity=0.6
    )]
    # TODO: bug! this is called rarely and does not work, because the range is not the xaxis lim!!!
    if 'range' in HR_plot_figure['layout']['xaxis'].keys():
        HR_plot_range = HR_plot_figure['layout']['xaxis']['range']
        idx = (data[file_name]['Time_stamp'] > pd.to_datetime(HR_plot_range[0])) & \
              (data[file_name]['Time_stamp'] < pd.to_datetime(HR_plot_range[1]))
        plot_selected_data = go.Histogram(
            y=dff.loc[idx, 'HR'].values,
            marker=dict(
                color='#FFD7E9'
            ),
            histnorm='probability',
            name='Selected range',
            opacity=0.6
        )
        plot_data.append(plot_selected_data)

    return {'data': plot_data,
            'layout': go.Layout(
                title='HR (bpm)',
                barmode='overlay'
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
                'color':('rgb(30, 30, 30)'),
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


def resample_df(df):
    if len(df.index) < 1000:
        return df

    step = int(len(df.index) / 1000)
    idx_keep = np.arange(0, len(df.index), step)
    return df.loc[idx_keep]




if __name__ == '__main__':
    app.config.supress_callback_exceptions = True
    app.run_server()
