import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc

from callbacks.loopt_tt_callbacks.manage_article_nodes import *
from callbacks.loopt_tt_callbacks.select_individual_node import *

dash.register_page(__name__, path="/looptt")

layout = html.Div([

    html.Div(id="dummy_callback"),
    html.Div(
        dash_table.DataTable(
            id="loop_tt_article_tb",
            style_table={"overflowX": "auto", "overflowY": "auto", "height":"500px"},
            page_size=30,
            style_data_conditional=[
                {
                    "if": {
                        "column_id": "id",
                        "filter_query": "{{{}}} is blank".format('point')
                    }, 
                    'backgroundColor': 'tomato'
                }
            ]
        ), 
        style={'margin': '1rem'}
    ),

    html.Div(id="selected_article_node", style={'margin': '1rem'})
    

])

