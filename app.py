from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def intro():
    return render_template('flaskr/flaskr/templates/intro.html')


@app.route('/hello')
def hello():
    return 'Hello, World'


if __name__ == '__main__':
    app.run()
