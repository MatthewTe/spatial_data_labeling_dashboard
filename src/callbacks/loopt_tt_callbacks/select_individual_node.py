import dash
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, html, dcc, ctx

import dash_bootstrap_components as dbc
from neo4j import GraphDatabase
import dash_leaflet as dl
import json
import pandas as pd
import geopandas as gpd

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
        edit_layer_children.append(dl.Marker(position=[selected_article['point'].y, selected_article['point'].x]))

    # Loading in all tt cities:
    all_tt_cities_df = pd.read_csv("./data/tt_cities.csv")
    all_tt_city_values = all_tt_cities_df['city'].to_list()

    # Loading all roads:
    all_tt_roads_df = pd.read_csv("./data/all_roads_tt.csv")
    all_roads_lst = all_tt_roads_df['name'].unique()

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
        ]),

        dbc.Row([
            dbc.Col([
                html.H5("City:"),
                dcc.Dropdown(id='trinidad_cities_dropdown', options=all_tt_city_values) 
            ]),
            dbc.Col([
                html.H5("Road:"),
                dcc.Dropdown(id='trinidad_roads_dropdown', options=all_roads_lst) 
            ])
       ], style={'margin': '1rem'}),

        dbc.Row(
            id="tt_location_map_parent_container",
            children=[
            dl.Map(children=[
                dl.TileLayer(),
                dl.FeatureGroup(edit_layer_children)],
                id='tt_location_inital_map',
                center=[10, -61],
                zoom=10,
                style={'height': '70vh'}
            )]
        ),

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

    updated_record_components = html.Div([

        dbc.Row(html.H4(f"{records[0].data()['n']['title']} updated")),

        html.Pre(json.dumps(records[0].data()['n'], indent=4)),

        dl.Map(
            [
            dl.TileLayer(),
            dl.Marker(position=[records[0].data()['n']['point'].y,records[0].data()['n']['point'].x])
            ],
            center=[10, -61],
            zoom=10,
            style={'height': '70vh'}
        )   
    ])

    return updated_record_components

@dash.callback(
    Output("tt_location_inital_map", "center"),
    Output("tt_location_inital_map", "zoom"),

    Input("trinidad_cities_dropdown", "value"),
    Input("trinidad_roads_dropdown", "value"),

    State("tt_location_inital_map", "children")
)
def zoom_to_city_or_road(selected_city: str | None, selected_road: str | None, map_children: list):
    
    if ctx.triggered_id == "trinidad_cities_dropdown":

        if selected_city is None:
            raise PreventUpdate
        
        cities_df = pd.read_csv("./data/tt_cities.csv")
        city_row = cities_df[cities_df['city'] == selected_city]
        city_lat, city_lon = city_row['lat'].iloc[0], city_row['lng'].iloc[0]

        return [city_lat, city_lon], 12

    elif ctx.triggered_id == "trinidad_roads_dropdown":

        roads_gdf = gpd.read_file("./data/hotosm_tto_roads_lines_shp.shp")
        selected_road = roads_gdf[roads_gdf['name'] == selected_road]

        road_linestring = selected_road['geometry'].iloc[0]
        road_start_vertex = road_linestring.coords[0]

        return [road_start_vertex[1], road_start_vertex[0]], 18

    else:
        raise PreventUpdate

def zoom_to_road(selected_road: str | None):

    if selected_road is None:
        raise PreventUpdate

