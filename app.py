"""
python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip

pip install dash
pip install dash-bootstrap-components
pip install PyQtWebEngine
pip install git+git://github.com/widdershin/flask-desktop.git
python -m pip install --upgrade Flask

pip install pyorbital
pip install requests
"""

import datetime
import webbrowser
from threading import Timer

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output, State

from webui import WebUI # Add WebUI to your imports
from PyQt5 import QtCore

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

"""
setattr(app, 'run', app.run_server)
#ui = WebUI(app, debug=True) # Create a WebUI instance
ui = WebUI(app, app_name='Dash + PyQtWebEngine teszt') # Create a WebUI instance
ui.view.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
"""

from pyorbital.orbital import Orbital
satellite = Orbital('TERRA')

modal = html.Div(
    [
        dbc.Button("Open modal", id="open"),
        dbc.Modal(
            [
                dbc.ModalHeader("Header"),
                dbc.ModalBody("This is the content of the modal"),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
        ),
    ]
)
                
app.layout = html.Div(
    [html.Div([
        html.H4('TERRA Satellite Live Feed'),
        html.Div(id='live-update-text'),
        dcc.Graph(
            id='live-update-graph',
            config={
                'displaylogo': False,
                #'displayModeBar': False,
                'modeBarButtonsToRemove': ['toImage',]
            }),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ]),
    modal
    ]
)

@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    lon, lat, alt = satellite.get_lonlatalt(datetime.datetime.now())
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Longitude: {0:.2f}'.format(lon), style=style),
        html.Span('Latitude: {0:.2f}'.format(lat), style=style),
        html.Span('Altitude: {0:0.2f}'.format(alt), style=style)
    ]


# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    satellite = Orbital('TERRA')
    data = {
        'time': [],
        'Latitude': [],
        'Longitude': [],
        'Altitude': []
    }

    # Collect some data
    for i in range(180):
        time = datetime.datetime.now() - datetime.timedelta(seconds=i*20)
        lon, lat, alt = satellite.get_lonlatalt(
            time
        )
        data['Longitude'].append(lon)
        data['Latitude'].append(lat)
        data['Altitude'].append(alt)
        data['time'].append(time)

    # Create the graph with subplots
    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

    fig.append_trace({
        'x': data['time'],
        'y': data['Altitude'],
        'name': 'Altitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': data['Longitude'],
        'y': data['Latitude'],
        'text': data['time'],
        'name': 'Longitude vs Latitude',
        'mode': 'lines+markers',
        'type': 'scatter'
    }, 2, 1)

    return fig

port = 8050 # or simply open on the default `8050` port

def open_browser():
	webbrowser.open_new(f"http://localhost:{port}")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server(debug=True, port=port)
    #ui.run() #replace app.run() with ui.run(), and that's it
