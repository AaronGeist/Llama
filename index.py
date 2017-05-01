from flask import Flask, render_template, jsonify

from biz.rpi import CpuTemperature, Memory

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Hello World'


@app.route('/name/<username>')
def hellouser(username):
    return 'Hello %s' % username


@app.route('/monitor/', methods=['GET', 'POST'])
def monitor():
    return render_template('monitor/index.html')


@app.route('/monitor/cpu/temperature', methods=['GET', 'POST'])
def monitor_cpu_temperature():
    return jsonify(CpuTemperature().history())


@app.route('/monitor/cpu/temperature/1', methods=['GET', 'POST'])
def monitor_cpu_temperature_single():
    return jsonify(CpuTemperature().latest())


@app.route('/monitor/memory/usage', methods=['GET', 'POST'])
def monitor_memory_usage():
    return jsonify(Memory().history())


@app.route('/monitor/memory/usage/1', methods=['GET', 'POST'])
def monitor_memory_usage_single():
    return jsonify(Memory().latest())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
