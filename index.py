from flask import Flask, render_template, jsonify

from biz.pt.putao import MagicPointChecker, UploadMonitor
from biz.rpi import CpuTemperature, Memory
#from physics.camera import Camera
#from physics.servo import Servo

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


@app.route('/monitor/cpu/temperature/', methods=['GET', 'POST'])
def monitor_cpu_temperature():
    return jsonify(CpuTemperature().history())


@app.route('/monitor/cpu/temperature/1/', methods=['GET', 'POST'])
def monitor_cpu_temperature_single():
    return jsonify(CpuTemperature().latest())


@app.route('/monitor/memory/usage/', methods=['GET', 'POST'])
def monitor_memory_usage():
    return jsonify(Memory().history())


@app.route('/monitor/memory/usage/1/', methods=['GET', 'POST'])
def monitor_memory_usage_single():
    return jsonify(Memory().latest())


@app.route('/monitor/magicpoint/', methods=['GET', 'POST'])
def monitor_magicpoint():
    return jsonify(MagicPointChecker().history())


@app.route('/monitor/magicpoint/1/', methods=['GET', 'POST'])
def monitor_magicpoint_single():
    return jsonify(MagicPointChecker().latest())

@app.route('/monitor/upload/', methods=['GET', 'POST'])
def monitor_upload():
    return jsonify(UploadMonitor().history())


@app.route('/monitor/upload/1/', methods=['GET', 'POST'])
def monitor_upload_single():
    return jsonify(UploadMonitor().latest())

'''
def gen(camera):
    while True:
        #print("take snapshot")
        frame = camera.snapshot()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # sleep to make sure frame generation speed could match the show speed
        time.sleep(0.05)


@app.route('/monitor/camera/', methods=['GET', 'POST'])
def monitor_camera():
    return render_template('monitor/camera.html')


@app.route('/monitor/camera/servo/', methods=['POST'])
def monitor_camera_servo():
    direction = request.form['direction']
    if direction == "left":
        Servo.left()
    elif direction == "right":
        Servo.right()
    return ""

@app.route('/monitor/camera/face/', methods=['GET'])
def monitor_camera_face():
    return str(Camera.is_enable_face_detect())

@app.route('/monitor/camera/face/set/', methods=['POST'])
def monitor_camera_face_set():
    enable = request.form['enable']
    if enable == "true":
        Camera.enable_face_detect()
    else:
        Camera.disable_face_detect()
    return ""


@app.route('/monitor/camera/brightness/get/', methods=['GET'])
def monitor_camera_brightness_get():
    return str(Camera.getBrightness())


@app.route('/monitor/camera/brightness/set/', methods=['POST'])
def monitor_camera_brightness_set():
    delta = request.form['delta']
    Camera.setBrightness(delta)
    return ""


@app.route('/camera/', methods=['GET', 'POST'])
def camera():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
