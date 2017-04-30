from flask import Flask, render_template, jsonify, Response, request

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello World'


@app.route('/name/<username>')
def hellouser(username):
    return 'Hello %s' % username


@app.route('/monitor/', methods=['GET'])
def monitor():
    return render_template('monitor/index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
