import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from noelTexturesPy import __version__ as app_version

jumbotron = html.Div(
    dbc.Container(
        [
            html.H1('noelTexturesPy', className='display-3'),
            html.H2('texture maps pipeline'),
            html.P(
                'generate texture maps from T1-weighted MRI',
                className='lead',
            ),
        ],
        fluid=False,
        style={'height': '20%'},
    ),
    className='p-3 bg-light rounded-3',
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Input(
                            id='case-id-input', placeholder='Enter case ID', type='text'
                        ),
                        html.Br(),
                        html.P(id='case-id-output', style={'display': 'none'}),
                        html.H2('Upload'),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div(
                                ['Drag and drop or click to select a file to upload.']
                            ),
                            style={
                                'width': '100%',
                                'height': '10%',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px',
                            },
                            multiple=True,
                        ),
                        html.H2('Texture Maps'),
                        html.Ul(
                            id='file-list',
                            style={
                                'width': '100%',
                                'height': '50%',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px',
                                'margin-top': '10px',
                            },
                        ),
                        dcc.Interval(
                            id='interval1', interval=1.000 * 1000, n_intervals=0
                        ),
                        dcc.Interval(
                            id='interval2', interval=1.001 * 1000, n_intervals=0
                        ),
                        html.H4(id='div-out', children=''),
                        html.Iframe(
                            id='console-out',
                            srcDoc='',
                            style={
                                'width': '100%',
                                'height': '50%',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px',
                            },
                        ),
                        # add version information
                        html.Footer(
                            f'Version: {app_version}',
                            style={
                                'position': 'fixed',
                                'bottom': '10px',
                                'right': '10px',
                            },
                        ),
                    ],
                    lg=8,
                ),
            ]
        )
    ],
    className='mt-4',
)
