import base64
import os, sys, glob, shutil
import numpy as np
from urllib.parse import quote as urlquote

from flask import Flask, send_from_directory, send_file
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from image_processing_utils import noelTexturesPy, logger
from utils import find_logger_basefilename, random_case_id

log_filename = find_logger_basefilename(logger)
logger.info("log filename: {}".format(str(log_filename)))

template = os.path.join('./templates', 'mni_icbm152_t1_tal_nlin_sym_09a.nii.gz')
output_dir = os.path.join('./outputs')

UPLOAD_DIRECTORY = os.path.join('./uploads')

try:
    shutil.rmtree(UPLOAD_DIRECTORY)
    shutil.rmtree(output_dir)
except OSError as e:
    print("Warning: %s - %s." % (e.filename, e.strerror))

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    os.makedirs(output_dir)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
# app = dash.Dash(server=server, external_stylesheets=external_stylesheets)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])



@server.route("/download/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(output_dir, path, as_attachment=True)


jumbotron = dbc.Jumbotron(
    [
        dbc.Container(
            [
                html.H1("noelTexturesPy", className="display-3"),
                html.H2("texture maps pipeline"),
                html.P(
                    "generate texture maps from T1-weighted AND/OR T2-weighted MRI",
                    className="lead",
                ),
            ],
            fluid=False,
            style={"height": "20%"}
        )
    ],
    fluid=False,
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Input(id="case-id-input", placeholder="Enter case ID", type="text"),
                        html.Br(),
                        html.P(id="case-id-output", style={'display': 'none'}),
                        html.H2("Upload"),
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                ["Drag and drop or click to select a file to upload."]
                            ),
                            style={
                                "width": "100%",
                                "height": "10%",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                            },
                            multiple=True,
                        ),
                        html.H2("Texture Maps"),
                        html.Ul(
                                id="file-list",
                                style={
                                    'width':'100%',
                                    'height':'50%',
                                    "lineHeight": "60px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "margin": "10px",
                                    "margin-top": "10px",
                                    }
                                ),
                        dcc.Interval(id='interval1', interval=1.000 * 1000, n_intervals=0),
                        dcc.Interval(id='interval2', interval=1.001 * 1000, n_intervals=0),
                        html.H4(id='div-out', children=''),
                        html.Iframe(
                            id='console-out',
                            srcDoc='',
                            style={
                                'width':'100%',
                                'height':'50%',
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                                }
                            )
                    ],
                    lg=8,
                ),
            ]
        )
    ],
    className="mt-4",
)

app.layout = html.Div([jumbotron, body])
app.config['suppress_callback_exceptions']=True
app.css.append_css({'external_url': "https://use.fontawesome.com/releases/v5.8.2/css/all.css"})
# app.layout = html.Div(
#     [
#         html.H1("noelTexturesPy"),
#         html.H2("image processing pipeline"),
#         html.H2("Upload"),
#         dcc.Upload(
#             id="upload-data",
#             children=html.Div(
#                 ["Drag and drop or click to select a file to upload."]
#             ),
#             style={
#                 "width": "100%",
#                 "height": "60px",
#                 "lineHeight": "60px",
#                 "borderWidth": "1px",
#                 "borderStyle": "dashed",
#                 "borderRadius": "5px",
#                 "textAlign": "center",
#                 "margin": "10px",
#             },
#             multiple=True,
#         ),
#         html.H2("Processed Files and Archive"),
#         html.Ul(id="file-list"),
#         dcc.Interval(id='interval1', interval=1 * 1000,
#     n_intervals=0),
#         dcc.Interval(id='interval2', interval=1.01 * 1000,
#     n_intervals=0),
#         html.H4(id='div-out', children=''),
#         html.Iframe(id='console-out',srcDoc='',style={'width':
#     '100%','height':250})
#     ],
#     style={"max-width": "800px"},
# )


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path) and path.endswith(("nii.gz", "nii")):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/download/{}".format(urlquote(filename))
    return html.A(filename, href=location)


def list_files(output_dir=output_dir):
    f = []
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for name in filenames:
            if name.endswith(('nii.gz','nii','pdf')):
                f.extend(filenames)
    return sorted(set(f))


@app.callback(
    Output("case-id-output", "children"),
    [Input("case-id-input", "n_blur")],
    [State("case-id-input", "value")],
)
def output_text(nb, value):
    return value

@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents"), Input("case-id-output", "children")],
)
def update_output(uploaded_filenames, uploaded_file_contents, case_id, output_dir = output_dir, template = template, uploads_dir = UPLOAD_DIRECTORY):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()

    if len(files) == 0:
        # return [html.Li("No files generated yet!")]
        return [dbc.Button(
                    [  dbc.Spinner(size="sm", type="grow"), " No files generated yet! "],
                        color="success",
                        disabled=True,
                    )]
    elif len(files) == 1 or len(files) == 2:
        t1, t2 = None, None
        for file in files:
            if file.lower().find("t1") != -1:
                t1 = os.path.join(uploads_dir, file)
                logger.info("T1-weighted image detected: {}".format(file))
                print("T1-weighted image detected: {}".format(file))
            if file.lower().find("t2") != -1 or file.lower().find("flair") != -1:
                t2 = os.path.join(uploads_dir, file)
                logger.info("T2-weighted image detected: {}".format(file))
                print("T2-weighted image detected: {}".format(file))
    else:
        print("more than 2 modalities are not supported at this time")
        logger.warn("more than 2 modalities are not supported at this time")

    # id = output_text()
    if case_id is not None:
        logger.info("Case ID: {}".format(str(case_id)))
    else:
        case_id = random_case_id()
        logger.info("assigning randomly generated case ID")
        logger.info("case ID: {}".format(case_id))
    noelTexturesPy(id=str(case_id), t1=t1, t2=t2, output_dir=output_dir, template=template, usen3=False).file_processor()

    try:
        for f in glob.glob(os.path.join(uploads_dir, '*')):
            os.remove(f)
        # os.remove('./logs.log')
    except OSError as e:
        print("Warning: %s - %s." % (e.filename, e.strerror))

    outputs = list_files(output_dir=output_dir)

    return [html.Ul(
                    html.I(
                            file_download_link(filename),
                            className='fas fa-arrow-alt-circle-down fa-sm fa-fw'),
                            className='fa-ul',
                            style={"margin": "-20px", "textAlign": "left", "padding-left": "10px", "padding-right": "10px"}
                            )
            for filename in outputs]


@app.callback(Output('div-out', 'children'),
    [Input('interval1', 'n_intervals')])
def update_interval(n):
    orig_stdout = sys.stdout
    f = open(log_filename, 'a')
    sys.stdout = f
    # print('Intervals Passed: {}'.format(str(n)))
    sys.stdout = orig_stdout
    f.close()
    return 'Logs'

@app.callback(Output('console-out', 'srcDoc'),
    [Input('interval2', 'n_intervals')])
def update_output(n):
    file = open(log_filename, 'r')
    data=''
    lines = file.readlines()
    if lines.__len__()<=12:
        last_lines=lines
    else:
        last_lines = lines[-12:]
    for line in last_lines:
        data=data+line + '<BR>'
    file.close()
    return data

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=True, port=9999)
