    # app.py

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import dash
from layouts import layout
from callbacks import register_callbacks

app = dash.Dash(
    __name__,
    title="PoultryTwin Dashboard",
    suppress_callback_exceptions=True
)

app.layout = layout

register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)