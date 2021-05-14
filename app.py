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

server = OidcServer(__name__, oauth_server="https://auth.demo.pragmaticindustries.de/auth/realms/hugo-demo",
                    client_id="b0618f82-53d6-4168-91da-a394b4585124",
                    client_secret="46ee08f0-646b-4b19-896e-6fb70d5a39b3")

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

    html.Button(children="Klick mich", id="button"),

    html.Div(children="", id="companies"),


    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])


@app.callback(Output("headline", "children"), Input("headline", "n_clicks"))
def set_headline(n_clicks):
    return f"Hallo {server.oidc.user_getfield('email')} / {server.oidc.get_access_token()} / {g.oidc_id_token}"


@app.callback(Output("companies", "children"), Input("button", "n_clicks"))
def list_companies(n_clicks):
    # We can get the access token from the server
    auth_token = server.oidc.get_access_token()
    if not auth_token:
        return "Fehler beim Login"

    configuration = openapi_client.Configuration(
        host="https://hugo-staging.pragmaticindustries.com/api"
    )
    client = ApiClient(configuration=configuration, header_name="Authorization",
                       header_value=f"Bearer {auth_token}")
    companies_api = CompaniesApi(client)
    result = companies_api.companies_list()

    return str(result)


if __name__ == '__main__':
    # Just start the server
    server.run()
