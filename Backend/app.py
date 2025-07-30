import flask

app = flask.Flask(__name__)

@app.route('/')
def home():
    return "Welcome to Crimes Against Foodies!"

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/admin')
def admin():
    flask.render_template('admin/index.html')