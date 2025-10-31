from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
from helpers import get_vms, enrich_vms_metrics

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/vms")
def api_vms():
    vms = get_vms()
    vms = enrich_vms_metrics(vms)
    return jsonify({"vms": vms})

def background_updates():
    """Emit VM data every 5 seconds"""
    import time
    while True:
        vms = get_vms()
        vms = enrich_vms_metrics(vms)
        socketio.emit("update_vms", {"vms": vms})
        time.sleep(5)

if __name__ == "__main__":
    socketio.start_background_task(background_updates)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
