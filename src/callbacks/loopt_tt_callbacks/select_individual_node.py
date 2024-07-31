import dash
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, html

import dash_bootstrap_components as dbc
from neo4j import GraphDatabase
import dash_leaflet as dl

from callbacks.global_callbacks.environment_management import load_environment_variables

@dash.callback(
    Output("selected_article_node", "children"),

    Input("loop_tt_article_tb", "active_cell"),
    State("global_environment_dropdown", "value")
)
def display_selected_article_node(active_cell: dict | None, environment: str):
    
    if active_cell is None:
        raise PreventUpdate

    env = load_environment_variables(environment)

    with GraphDatabase.driver(env['neo4j_url'], auth=(env['neo4j_username'], env['neo4j_password'])) as driver:
        driver.verify_connectivity()

    records, summary, keys = driver.execute_query(
        """MATCH (n:Article:LoopTT {id: $id}) 
        RETURN 
            n.id AS id, 
            n.title as title,
            n.type AS type, 
            n.content AS content,
            n.published_date AS published_date,
            coalesce(n.point, null) AS point

        
        """,
        parameters_={'id': active_cell['row_id']}
    )

    if len(records) != 1:
        print(f"Error: Neo4J Graph returns more than one record: {len(records)}")
        raise PreventUpdate

    selected_article = records[0].data()

    edit_layer_children = [
        dl.EditControl(
            id="selected_article_edit_point", 
        )
    ]

    if selected_article['point'] is not None:
        print(selected_article['point'], "HELLO WORLD")
        edit_layer_children.append(dl.Marker(position=[selected_article['point'].y, selected_article['point'].x]))

    # Full Title description component:
    selected_row_component = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    html.H4(selected_article['title'])
                ]),
                dbc.Row(html.Span(f"Published Date: {selected_article['published_date']}"), style={'margin-bottom':'0.5rem'}),
                dbc.Row([
                    html.P(selected_article['content'])
                ])
            ]),
            dbc.Col(
                dl.Map(children=[
                    dl.TileLayer(),
                    dl.FeatureGroup(edit_layer_children)],
                    center=[10, -61],
                    zoom=9,
                    style={'height': '70vh'}
                )
            )
        ]),

        dbc.Row(dbc.Button("Insert Node", id='insert_article_node_btn', n_clicks=0), style={'margin': "1rem"}),

        html.Div(id="update_node_output_component")

    ])

    return selected_row_component

@dash.callback(

    Output("update_node_output_component", "children"),

    Input("insert_article_node_btn", "n_clicks"),

    State("loop_tt_article_tb", "active_cell"),
    State("selected_article_edit_point", "geojson"),
    State("global_environment_dropdown", "value")
)
def save_or_update_article_node(n_clicks: int | None, active_cell: dict, existing_edit_geojson: dict, environment: str):

    if n_clicks == 0:
        raise PreventUpdate

    env = load_environment_variables(environment)

    # This is assuming a very specific data structure of the editing geojson:
    # {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'type': 'marker', '_leaflet_id': 144}, 'geometry': {'type': 'Point', 'coordinates': [-61.24877929687501, 10.506646628163548]}}]}
    geojson_geometry_point = existing_edit_geojson['features'][0]['geometry']['coordinates']
    lon, lat = geojson_geometry_point[0], geojson_geometry_point[1]

    with GraphDatabase.driver(env['neo4j_url'], auth=(env['neo4j_username'], env['neo4j_password'])) as driver:
        driver.verify_connectivity()

    records, summary, keys = driver.execute_query("""
        MATCH (n:Article:LoopTT {id: $id})
        SET n.point = point({latitude: $lat, longitude: $lon})
        RETURN n
        """,
        parameters_={
            'id': active_cell['row_id'], 
            'lat': lat,
            'lon': lon
        }
    )

    return html.Pre(str(records[0].data()))

   