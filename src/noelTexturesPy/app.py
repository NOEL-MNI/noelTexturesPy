#!/usr/bin/env python

import base64
import glob
import logging
import os
import sys
from urllib.parse import quote as urlquote

import dash_bootstrap_components as dbc
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from flask import Flask
from flask import send_from_directory

from noelTexturesPy.image_processing import case_id as random_case_id
from noelTexturesPy.image_processing import log_filename
from noelTexturesPy.image_processing import logger
from noelTexturesPy.image_processing import noelTexturesPy
from noelTexturesPy.layout import body
from noelTexturesPy.layout import jumbotron

template = os.path.join('./templates', 'mni_icbm152_t1_tal_nlin_sym_09a.nii.gz')

TEMPDIR = os.environ.get('TEMPDIR')
assert TEMPDIR is not None
output_dir = os.path.join(TEMPDIR, 'outputs')
upload_directory = os.path.join(TEMPDIR, 'uploads')

if not os.path.exists(upload_directory):
    os.makedirs(upload_directory)
    os.makedirs(output_dir)


# normally, Dash creates its own Flask server internally - by creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'noelTexturesPy'

# initialize a logger to prevent flask from logging to console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.layout = html.Div([jumbotron, body])
app.config['suppress_callback_exceptions'] = True
app.logger.disabled = True
app.css.append_css(
    {'external_url': 'https://use.fontawesome.com/releases/v5.8.2/css/all.css'}
)


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode('utf8').split(b';base64,')[1]
    with open(os.path.join(upload_directory, name), 'wb') as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(upload_directory):
        path = os.path.join(upload_directory, filename)
        if os.path.isfile(path) and path.endswith(('nii.gz', 'nii')):
            files.append(filename)
    return files


@server.route('/download/<path:path>')
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(output_dir, path, as_attachment=True)


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = f'/download/{urlquote(filename)}'
    return html.A(filename, href=location)


def list_files(output_dir=output_dir):
    f = []
    for _, _, filenames in os.walk(output_dir):
        for name in filenames:
            if name.endswith(('nii', 'pdf')):
                f.extend(filenames)
    return sorted(set(f))


@callback(
    Output('case-id-output', 'children'),
    [Input('case-id-input', 'n_blur')],
    [State('case-id-input', 'value')],
)
def output_text(nb, value):
    return value


@callback(
    Output('file-list', 'children'),
    [
        Input('upload-data', 'filename'),
        Input('upload-data', 'contents'),
        Input('case-id-output', 'children'),
    ],
)
def update_output(
    uploaded_filenames,
    uploaded_file_contents,
    case_id,
    output_dir=output_dir,
    template=template,
    uploads_dir=upload_directory,
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
                [dbc.Spinner(size='sm', type='grow'), ' No files generated yet! '],
                color='success',
                disabled=True,
            )
        ]
    elif len(files) == 1 or len(files) == 2:
        t1, t2 = None, None
        for file in files:
            if file.lower().find('t1') != -1:
                t1 = os.path.join(uploads_dir, file)
                logger.info(f'T1-weighted image detected: {file}')
                print(f'T1-weighted image detected: {file}')
            if file.lower().find('t2') != -1 or file.lower().find('flair') != -1:
                t2 = os.path.join(uploads_dir, file)
                logger.info(f'T2-weighted image detected: {file}')
                print(f'T2-weighted image detected: {file}')
    else:
        print('more than 2 modalities are not supported at this time')
        logger.warning('more than 2 modalities are not supported at this time')

    # id = output_text()
    if case_id is not None:
        logger.info(f'Case ID: {str(case_id)}')
    else:
        case_id = random_case_id
        logger.info('assigning randomly generated case ID')
        logger.info(f'case ID: {case_id}')
    noelTexturesPy(
        id=str(case_id),
        t1=t1,
        t2=t2,
        output_dir=output_dir,
        temp_dir=TEMPDIR,
        template=template,
        usen3=False,
    ).file_processor()

    try:
        for f in glob.glob(os.path.join(uploads_dir, '*')):
            os.remove(f)
    except OSError as e:
        print(f'Warning: {e.filename} - {e.strerror}.')

    outputs = list_files(output_dir=output_dir)

    return [
        html.Ul(
            html.I(
                file_download_link(filename),
                className='fas fa-arrow-alt-circle-down fa-sm fa-fw',
            ),
            className='fa-ul',
            style={
                'margin': '-20px',
                'textAlign': 'left',
                'padding-left': '10px',
                'padding-right': '10px',
            },
        )
        for filename in outputs
    ]


@callback(Output('div-out', 'children'), [Input('interval1', 'n_intervals')])
def update_interval(n):
    orig_stdout = sys.stdout
    f = open(log_filename, 'a')
    sys.stdout = f
    sys.stdout = orig_stdout
    f.close()
    return 'Logs'


@callback(Output('console-out', 'srcDoc'), [Input('interval2', 'n_intervals')])
def update_console(n):
    file = open(log_filename)
    data = ''
    lines = file.readlines()
    if lines.__len__() <= 14:
        last_lines = lines
    else:
        last_lines = lines[-14:]
    for line in last_lines:
        data = data + line + '<BR>'
    file.close()
    return data


def run_server():
    app.run_server(host='0.0.0.0', debug=False, port=9999)


def run_debug_server():
    app.run_server(host='0.0.0.0', debug=True, port=9999)


if __name__ == '__main__':
    run_server()
