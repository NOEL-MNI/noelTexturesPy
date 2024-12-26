import base64, glob, logging, os, shutil, sys
from urllib.parse import quote as urlquote

from flask import Flask, send_from_directory
import dash_bootstrap_components as dbc
from dash import Dash, callback, html, dcc, Input, Output, State, MATCH, ALL

from image_processing import noelTexturesPy, logger
from utils import find_logger_basefilename, random_case_id

log_filename = find_logger_basefilename(logger)
logger.info("log filename: {}".format(str(log_filename)))

template = os.path.join("./templates", "mni_icbm152_t1_tal_nlin_sym_09a.nii.gz")
output_dir = os.path.join("./outputs")

UPLOAD_DIRECTORY = os.path.join("./uploads")

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
app = Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "noelTexturesPy"

# initialize a logger to prevent flask from logging to console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.layout = html.Div([jumbotron, body])
app.config["suppress_callback_exceptions"] = True
app.css.append_css(
    {"external_url": "https://use.fontawesome.com/releases/v5.8.2/css/all.css"}
)


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
            if name.endswith(("nii", "pdf")):
                f.extend(filenames)
    return sorted(set(f))


@callback(
    Output("case-id-output", "children"),
    [Input("case-id-input", "n_blur")],
    [State("case-id-input", "value")],
)
def output_text(nb, value):
    return value


@callback(
    Output("file-list", "children"),
    [
        Input("upload-data", "filename"),
        Input("upload-data", "contents"),
        Input("case-id-output", "children"),
    ],
)
def update_output(
    uploaded_filenames,
    uploaded_file_contents,
    case_id,
    output_dir=output_dir,
    template=template,
    uploads_dir=UPLOAD_DIRECTORY,
):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)

    files = uploaded_files()

    if len(files) == 0:
        # return [html.Li("No files generated yet!")]
        return [
            dbc.Button(
                [dbc.Spinner(size="sm", type="grow"), " No files generated yet! "],
                color="success",
                disabled=True,
            )
        ]
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
    noelTexturesPy(
        id=str(case_id),
        t1=t1,
        t2=t2,
        output_dir=output_dir,
        template=template,
        usen3=False,
    ).file_processor()

    try:
        for f in glob.glob(os.path.join(uploads_dir, "*")):
            os.remove(f)
        # os.remove('./logs.log')
    except OSError as e:
        print("Warning: %s - %s." % (e.filename, e.strerror))

    outputs = list_files(output_dir=output_dir)

    return [
        html.Ul(
            html.I(
                file_download_link(filename),
                className="fas fa-arrow-alt-circle-down fa-sm fa-fw",
            ),
            className="fa-ul",
            style={
                "margin": "-20px",
                "textAlign": "left",
                "padding-left": "10px",
                "padding-right": "10px",
            },
        )
        for filename in outputs
    ]


@callback(Output("div-out", "children"), [Input("interval1", "n_intervals")])
def update_interval(n):
    orig_stdout = sys.stdout
    f = open(log_filename, "a")
    sys.stdout = f
    # print('Intervals Passed: {}'.format(str(n)))
    sys.stdout = orig_stdout
    f.close()
    return "Logs"


@callback(Output("console-out", "srcDoc"), [Input("interval2", "n_intervals")])
def update_output(n):
    file = open(log_filename, "r")
    data = ""
    lines = file.readlines()
    if lines.__len__() <= 14:
        last_lines = lines
    else:
        last_lines = lines[-14:]
    for line in last_lines:
        data = data + line + "<BR>"
    file.close()
    return data


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", debug=False, port=9999)