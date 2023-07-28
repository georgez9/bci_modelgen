from dash import Dash, dcc, html, Input, Output, callback
from figures import init_figs
from tcp_server import tcp_client_processing
from multiprocessing import Process, Manager, Queue
import numpy as np
from analysis import baseline_shift, filtered, show_psd


my_global_fig, my_psd_fig = init_figs()
realtime_flag = False

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
                    "label": html.Div(["File"], className="nav-item", id="nav-item-1"),
                    "value": "File"
                },
                {
                    "label": html.Div(["Real-Time"], className="nav-item", id="nav-item-2"),
                    "value": "Real-Time"
                }
            ], id="select-model", value="File", inline=True, className="nav", inputClassName="nav-rad"),
        ], style={'textAlign': 'left', 'width': '50%', 'padding-top': '20px', 'padding-left': '50px'}),
        html.Div([
            html.Button('Start', id='start-stop-button', n_clicks=0),
            html.Button('Exit', id='exit-button', n_clicks=0),
        ], style={'textAlign': 'right', 'width': '50%', 'padding-top': '20px', 'padding-right': '50px'})
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([dcc.Graph(id='sample-graph', figure=my_global_fig)], className="global-graph-graph"),
        dcc.Interval(id='interval-component', interval=1 * 1000, n_intervals=0, disabled=True),
        html.Div([
            dcc.RangeSlider(min=0, max=10, value=[0, 10],
                            tooltip={"placement": "bottom", "always_visible": True},
                            id='my-range-slider')
        ], className="range-slider", )
    ]),
    html.Div([
        html.Div([dcc.Graph(id='psd-graph', figure=my_psd_fig, className='psd-graph-graph')], className="psd-graph"),
        html.Div([
            html.Div([], className='dash-board-frame')
        ], className='dash-board')
    ], style={'display': 'flex'})
])


# Callback functions
# for choosing the data analyse mode
@app.callback(
    Output('nav-item-1', 'style'),
    Output('nav-item-2', 'style'),
    Output('my-range-slider', 'value'),
    Output('interval-component', 'disabled'),
    Input('select-model', 'value'),
    Input('my-range-slider', 'value'))
def update_model(value, value1):
    global realtime_flag
    if value == "Real-Time":
        realtime_flag = True
        # processing for tcp/ip function
        tcp_processing.start()
        return {'background-color': 'white', 'color': 'black'}, {'background-color': '#163a6c', 'color': 'white'}, \
            [8, 9], False
    if value == "File":
        if realtime_flag:
            realtime_flag = False
            tcp_processing.join()
        return {'background-color': '#163a6c', 'color': 'white'}, {'background-color': 'white', 'color': 'black'}, \
            value1, True


@app.callback(
    Output('start-stop-button', 'n_clicks'),
    Output('exit-button', 'n_clicks'),
    Input('start-stop-button', 'n_clicks'),
    Input('exit-button', 'n_clicks'),
)
def button_clicked(start_stop_clicks, exit_clicks):
    if not exit_clicks > 0:
        if start_stop_clicks > 0:
            if start_stop_clicks % 2 == 0:
                q.put('1')  # stop
            else:
                q.put('0')  # start
    else:
        q.put('2')
        tcp_processing.join()

    return start_stop_clicks, exit_clicks


@callback(
    Output('sample-graph', 'figure'),
    Output('psd-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_metrics(n):
    data_list = list(d)
    array_length = 10000
    my_global_fig.update_traces(
        x=np.linspace(0, 11, array_length),
        y=data_list,
    )
    bs_data = baseline_shift(data_list, t_start=8, t_end=9)
    filter_data = filtered(bs_data, f1=3, f2=30, sr=1000)
    psd_data = show_psd(filter_data, welch_tw=0.8, sr=1000)
    my_psd_fig.update_traces(
        x=psd_data[0],
        y=psd_data[1],
    )
    return my_global_fig, my_psd_fig


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # shared variables between dash app and tcp/ip server
    with Manager() as manager:
        d = Manager().list()  # raw datas
        q = Queue()  # control signal
    tcp_processing = Process(target=tcp_client_processing, args=(d, q))
    # dash app run
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
