from app import app

from components import default_layout as dl
from components import dashboard as db

app.layout = dl.default_layout(db.layout)


if __name__ == '__main__':
    app.run_server(debug=True)