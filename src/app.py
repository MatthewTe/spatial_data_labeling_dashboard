import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)




app.layout = html.Div([

    dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(dbc.NavbarBrand("Dashboard", className="ms-2")),
                            
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://plotly.com",
                    style={"textDecoration": "none"},
                ),

                dcc.Dropdown(
                    id="global_environment_dropdown", 
                    options=['Test', 'Dev', "Prod"],
                    value="Test",
                    style={'width': '200px'},
                    persistence=True
                )

            ] + [

                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Div(
                                dcc.Link(f"{page['name']} - {page['path']}", href=page['relative_path'])
                            ))
                        ]
                    )
                )
                for page in dash.page_registry.values()
            ]
        ),
        color="dark",
        dark=True,
    ),

    dash.page_container
])


if __name__ == '__main__':
    app.run(debug=True)