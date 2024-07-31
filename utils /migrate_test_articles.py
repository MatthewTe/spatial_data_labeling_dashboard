from neo4j import GraphDatabase
import sqlalchemy as sa
import pandas as pd

URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "test_password")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

sqlite_engine = sa.create_engine("sqlite:////Users/matthewteelucksingh/Repos/TT_info_classifier/data/dev_db.sqlite3")

with sqlite_engine.connect() as conn, conn.begin():

    query = sa.text("SELECT * FROM articles")
    df = pd.read_sql(query, conn)

for index, row in df.iterrows():
    records, summary, keys = driver.execute_query("""
        CREATE (a:Article:LoopTT {
            id: $id,
            title: $title,
            url: $url,
            type: $type,
            content: $content,
            source: $source,
            extracted_date: $extracted_date,
            published_date: $published_date
        })
    """, 
    id=row['id'], 
    title=row['title'],
    url=row['url'],
    type=row['type'],
    content=row['content'],
    source=row['source'],
    extracted_date=row['extracted_date'],
    published_date=row['published_date']
    )