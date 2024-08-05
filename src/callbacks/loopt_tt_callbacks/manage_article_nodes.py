import dash
from dash import Input, Output, State
from neo4j import GraphDatabase

from callbacks.global_callbacks.environment_management import load_environment_variables

@dash.callback(
    
    Output("loop_tt_article_tb", "columns"),
    Output("loop_tt_article_tb", "data"),

    Input("dummy_callback", "children"),
    State("global_environment_dropdown", "value")
)
def load_all_article_nodes(_, environment: str | None):

    env: dict = load_environment_variables(environment)

    print(env['neo4j_url'], (env['neo4j_username'], env['neo4j_password']))

    with GraphDatabase.driver(env['neo4j_url'], auth=(env['neo4j_username'], env['neo4j_password'])) as driver:
        driver.verify_connectivity()

    records, summary, keys = driver.execute_query(
    """
        MATCH (n:Article:LoopTT) 
        RETURN 
            n.id AS id, 
            n.title as title,
            n.type AS type, 
            n.published_date AS published_date,
            toString(coalesce(n.point, null)) AS point,
            coalesce(n.h3Index, null) AS h3Index
    """
    )
    
    rows = [article.data() for article in records]

    columns = [
        {'name': "id", "id": "id"},
        {'name': "title", "id": "title"},
        {'name': "point", "id": "point"},
        {'name': "h3Index", "id": "h3Index"},
        {'name': "type", "id": "type"},
        {'name': "published_date", "id": "published_date"},
    ]

    return columns, rows