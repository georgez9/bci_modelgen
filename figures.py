import numpy as np
import pandas as pd
import plotly.graph_objs as go


def init_figs():
    # global figure
    array_length = 10000
    df = pd.DataFrame({"t/s": np.linspace(0, 11, array_length), "uV": np.zeros(array_length)})
    global_fig = go.Figure(data=[go.Scatter(x=df["t/s"], y=df["uV"], name='Data 1')])
    # print(df["t/s"])
    global_fig.update_layout(autosize=False, width=1400, height=400, plot_bgcolor='white',
                             paper_bgcolor='rgba(0,0,0,0)')
    global_fig.update_traces(line=dict(color="#CF382A", width=1))
    global_fig.update_xaxes(gridcolor="#B8B8B8")
    global_fig.update_yaxes(range=[-80, 80], gridcolor="#B8B8B8")

    df = pd.DataFrame({"f/Hz": np.linspace(0, 51), "P": np.zeros(50)})
    psd_fig = go.Figure(data=[go.Scatter(x=df["f/Hz"], y=df["P"], mode='lines', line=dict(color='blue', width=1.5))])

    psd_fig.update_layout(shapes=[
        dict(type="rect", xref="x", yref="paper", x0=8, y0=0, x1=15, y1=1, fillcolor="#CF8B2A",  # background
             opacity=0.5, layer="below", line_width=0,
             )
    ], autosize=False, width=500, height=400, plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',)
    psd_fig.update_traces(line=dict(color="#CF382A", width=1.5), fill='tozeroy')
    psd_fig.update_xaxes(gridcolor="#B8B8B8", range=[0, 60])
    psd_fig.update_yaxes(range=[0, 5])

    return global_fig, psd_fig
