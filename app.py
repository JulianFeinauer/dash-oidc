from typing import List, Optional

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash import dash
from dash.dependencies import Output, Input
from flask import g

import openapi_client
from openapi_client import ApiClient
from openapi_client.api.companies_api import CompaniesApi
from oidc_server import OidcServer
from openapi_client.api.machines_api import MachinesApi
from openapi_client.api.telemetry_api import TelemetryApi
from openapi_client.model.company import Company
from openapi_client.model.machine import Machine

server = OidcServer(__name__, oauth_server="https://auth.demo.pragmaticindustries.de/auth/realms/hugo-demo",
                    client_id="b0618f82-53d6-4168-91da-a394b4585124",
                    client_secret="46ee08f0-646b-4b19-896e-6fb70d5a39b3")


def get_api_client(access_token) -> Optional[ApiClient]:
    if not access_token:
        print("Fehler beim Login")
        return None

    configuration = openapi_client.Configuration(
        host="https://hugo-staging.pragmaticindustries.com/api"
    )
    client = ApiClient(configuration=configuration, header_name="Authorization",
                       header_value=f"Bearer {access_token}")

    return client


# Build a regular Dash app, only pass the server...
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Hello Dash', id="headline"),

    dcc.Interval(id='interval-component', interval=1000 * 1000, n_intervals=0),

    html.Div(children="", id="companies"),

    dcc.Dropdown(
        id='companies-dropdown',
        options=[
        ],
    ),

    dcc.Dropdown(
        id='machine-dropdown',
        options=[
        ],
    ),

    html.Div(children='''
        Dash: A web application framework for Python.
    ''', id="welcome"),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])


@app.callback(Output("headline", "children"), Input("interval-component", "n_intervals"))
def set_headline(n):
    return f"Hallo {server.oidc.user_getfield('email')}!"


@app.callback(Output("welcome", "children"), Input("companies-dropdown", "value"))
def update_text(value):
    if value is not None:
        client = get_api_client(server.oidc.get_access_token())
        if client:
            companies_api = CompaniesApi(client)

            company: Company = companies_api.companies_read(id=value)
            return f"Sie haben das Unternehmen {company.name} ausgewählt!"
    else:
        return "Bitte wählen Sie ein Unternehmen aus!"


@app.callback(Output("machine-dropdown", "options"), Input("companies-dropdown", "value"))
def list_tv(company):
    client = get_api_client(server.oidc.get_access_token())
    if client:
        machine_api = MachinesApi(client)
        result: List[Machine] = machine_api.machines_list(owner=str(company))

        values = [{"label": r.name, "value": r.id} for r in result]

        return values


@app.callback(Output("companies-dropdown", "options"), Input("interval-component", "n_intervals"))
def list_companies(n):
    print("Refresh...")
    # We can get the access token from the server
    client = get_api_client(server.oidc.get_access_token())
    if client:
        companies_api = CompaniesApi(client)
        result: List[Company] = companies_api.companies_list()

        values = [{"label": r.name, "value": r.id} for r in result]

        return values


if __name__ == '__main__':
    # Just start the server
    server.run()
