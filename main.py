from dash import Dash, dcc, html, Input, Output, callback, State
from figures import init_figs
from tcp_server import tcp_client_processing
from multiprocessing import Process, Manager, Queue
import numpy as np
from analysis import baseline_shift, filtered, show_psd, clc_power
import datetime
from sklearn import preprocessing  # scale and center data
from sklearn.svm import SVC
from joblib import load
import pandas as pd
from data_extraction import output_psd_txt
from svm_training import svm_train

my_global_fig, my_psd_fig = init_figs()
realtime_flag = False
state_flag = 0

# Dash display
app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Img(src="./assets/ncl_logo.png", className='ncl-logo'),
        html.P(["Real-time Electroencephalogram Analysis System"], className="title"),
        html.Div([
            html.P(["George Zhao"], className="contact"),
            html.A(["Email: j.zhao36@newcastle.ac.uk"], className="contact", href='mailto:j.zhao36@newcastle.ac.uk')
        ])
    ], className="app-header"),
    html.Div([
        html.Div([
            dcc.RadioItems([
                {
                    "label": html.Div(["Wait"], className="nav-item", id="nav-item-1"),
                    "value": "Wait"
                },
                {
                    "label": html.Div(["Link"], className="nav-item", id="nav-item-2"),
                    "value": "Link"
                }
            ], id="select-model", value="Wait", inline=True, className="nav", inputClassName="nav-rad"),
        ], style={'textAlign': 'left', 'width': '50%', 'padding-top': '20px', 'padding-left': '50px'}),
        html.Div([
            html.Button('Start', id='start-stop-button', n_clicks=0),

        ], style={'textAlign': 'right', 'width': '50%', 'padding-top': '20px', 'padding-right': '50px'})
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([dcc.Graph(id='sample-graph', figure=my_global_fig)], className="global-graph-graph"),
        dcc.Interval(id='interval-component', interval=1 * 1000, n_intervals=0, disabled=True),
    ]),
    html.Div([
        html.Div([
            html.Div([
                html.Button('State 1', id='state1-button', n_clicks=0),
                html.Button('State 0', id='state2-button', n_clicks=0),
                html.Button('Exit', id='exit-button', n_clicks=0),
                html.Button('Train', id='train-button', n_clicks=0),
                html.Div([''], id='cvt-state'),
            ], className='dash-board-text'),
        ], className='dash-board-frame'),
    ], className='dash-board')
])


# Callback functions
# for choosing the data analyse mode
@app.callback(
    Output('cvt-state', 'children'),
    Input('train-button', 'n_clicks'),
)
def training_model(click):
    if click>0:
        output_psd_txt('./data/state1.txt')
        output_psd_txt('./data/state2.txt')

        return svm_train()
    return f'0'



@app.callback(
    Output('nav-item-1', 'style'),
    Output('nav-item-2', 'style'),
    Output('interval-component', 'disabled'),
    Input('select-model', 'value'),
)
def update_model(value):
    global realtime_flag
    if value == "Link":
        realtime_flag = True
        # processing for tcp/ip function
        tcp_processing.start()
        return {'background-color': 'white', 'color': 'black'}, {'background-color': '#163a6c', 'color': 'white'}, False
    if value == "Wait":
        if realtime_flag:
            realtime_flag = False
            tcp_processing.join()
        return {'background-color': '#163a6c', 'color': 'white'}, {'background-color': 'white', 'color': 'black'}, True


@app.callback(
    Output('state1-button', 'n_clicks'),
    Output('exit-button', 'n_clicks'),
    Input('state1-button', 'n_clicks'),
    Input('exit-button', 'n_clicks'),
    Input('select-model', 'value'),
)
def button_clicked(state1_clicks, exit_clicks, value):
    global state_flag
    if value == "Link":
        if not exit_clicks > 0:
            if state1_clicks > 0:
                if state1_clicks % 2 == 0:
                    q.put('1')  # stop
                    state_flag = 0
                else:
                    state_flag = 1
                    q.put('0')  # start
        else:
            q.put('2')
            tcp_processing.join()
    return state1_clicks, exit_clicks


@app.callback(
    Output('state2-button', 'n_clicks'),
    Input('state2-button', 'n_clicks'),
    Input('exit-button', 'n_clicks'),
    Input('select-model', 'value'),
)
def button_clicked1(state2_clicks, exit_clicks, value):
    global state_flag
    if value == "Link":
        if not exit_clicks > 0:
            if state2_clicks > 0:
                if state2_clicks % 2 == 0:
                    q.put('1')  # stop
                    state_flag = 0
                else:
                    q.put('0')  # start
                    state_flag = 2
        else:
            q.put('2')
            tcp_processing.join()
    return state2_clicks


@callback(
    Output('sample-graph', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('select-model', 'value'),
)
def update_metrics(n, value):
    data_list = list(d)
    if value == "Link" and data_list:
        array_length = 10000
        my_global_fig.update_traces(
            x=np.linspace(0, 11, array_length),
            y=data_list,
        )
        len_datalist = len(data_list)
        if len_datalist > 9999:
            bs_data = data_list[8*1000:9*1000]
            if state_flag == 1:
                with open('./data/state1.txt', 'a') as file1:
                    file1.write(str(bs_data))
            elif state_flag == 2:
                with open('./data/state2.txt', 'a') as file1:
                    file1.write(str(bs_data))
    return my_global_fig


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # with open('./data/state1.txt', 'w') as files1:
    #     pass
    # with open('./data/state2.txt', 'w') as files2:
    #     pass
    # shared variables between dash app and tcp/ip server
    with Manager() as manager:
        d = Manager().list()  # raw datas
        q = Queue()  # control signal
    tcp_processing = Process(target=tcp_client_processing, args=(d, q))
    # dash app run
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
