"""
python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip

pip install dash
pip install dash-bootstrap-components
pip install git+git://github.com/argabor/dash-desktop.git

pip install pyorbital
pip install requests
"""

port = 8050 # or simply open on the default `8050` port
DESKTOP_APP = True

import datetime

if not DESKTOP_APP:
    import webbrowser
    from threading import Timer
    def open_browser():
        webbrowser.open_new(f"http://localhost:{port}")

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

from dashui import DashUI # Add WebUI to your imports
from PyQt5 import QtCore

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

if DESKTOP_APP:
    ui = DashUI(app, app_name='DashUI test', showMaximized=False, icon_path='sample_icon.png') # Create a DashUI instance

from pyorbital.orbital import Orbital
satellite = Orbital('TERRA')

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Sidebar", className="display-4"),
        html.Hr(),
        html.P(
            "A simple sidebar layout with navigation links", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Page 1", href="/page-1", active="exact"),
                dbc.NavLink("Page 2", href="/page-2", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

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
            size="lg",
        ),
    ]
)

content = html.Div(
    id="page-content", 
    style=CONTENT_STYLE,
)

home_page = html.Div([html.Div([
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
    ],
)

page_1 = html.Div([
        html.H4('Using the Low-Level Interface'),
        html.P("This is page 1."),
        dcc.Graph(
            id='example-graph-2',
            config={
                'displaylogo': False,
                #'displayModeBar': False,
                'modeBarButtonsToRemove': ['toImage',]
            },
            figure=go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])
        )
    ]
)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return home_page
    elif pathname == "/page-1":
        return page_1
    elif pathname == "/page-2":
        return html.P("Oh cool, this is page 2!")
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )

@app.callback(Output("modal", "is_open"),
              [Input("open", "n_clicks"), Input("close", "n_clicks")],
              [State("modal", "is_open")])
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

if __name__ == '__main__':
    if DESKTOP_APP:   
        ui.run() #replace app.run() with ui.run(), and that's it
    else:
        Timer(1, open_browser).start()
        app.run_server(debug=True, port=port)
