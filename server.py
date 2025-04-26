from flask import Flask, Response, request, jsonify
import threading
import os

app = Flask(__name__)

# Store latest image and direction (thread-safe)
latest_image = None
image_lock = threading.Lock()
current_direction = 'none'  # Default direction
direction_lock = threading.Lock()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Drone Camera Stream</title>
        <style>
            #imageDisplay { display: block; margin: 0 auto; }
            #controls { text-align: center; margin-top: 10px; }
            button { padding: 10px 20px; margin: 5px; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>Drone Camera Feed</h1>
        <img src="/image_feed" id="imageDisplay" width="640" height="480">
        <div id="controls">
            <button onclick="sendDirection('up')">Up</button>
            <button onclick="sendDirection('down')">Down</button>
            <button onclick="sendDirection('left')">Left</button>
            <button onclick="sendDirection('right')">Right</button>
        </div>
        <script>
            function sendDirection(direction) {
                fetch('/set_direction', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({direction: direction})
                }).then(response => response.json())
                  .then(data => {
                      console.log('Direction set:', data.direction);
                  }).catch(error => {
                      console.error('Error setting direction:', error);
                  });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/upload_image', methods=['POST'])
def upload_image():
    global latest_image
    if 'image' not in request.files:
        return jsonify({'direction': 'none'}), 400
    image = request.files['image'].read()
    with image_lock:
        latest_image = image
    with direction_lock:
        direction = current_direction
    return jsonify({'direction': direction}), 200

@app.route('/set_direction', methods=['POST'])
def set_direction():
    global current_direction
    data = request.get_json()
    direction = data.get('direction', 'none')
    if direction not in ['up', 'down', 'left', 'right']:
        direction = 'none'
    with direction_lock:
        current_direction = direction
    return jsonify({'direction': direction}), 200

@app.route('/get_direction', methods=['GET'])
def get_direction():
    with direction_lock:
        direction = current_direction
    return jsonify({'direction': direction}), 200

@app.route('/image_feed')
def image_feed():
    with image_lock:
        if latest_image is None:
            # Return a blank image if none available
            blank_image = b'\xFF' * (640 * 480 * 3)  # Dummy data
            return Response(blank_image, mimetype='image/jpeg')
        return Response(latest_image, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), threaded=True)
