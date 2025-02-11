from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading
import time

# Initialize Flask app
app = Flask(__name__)

# Define routes after app initialization
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    try:
        video_url = request.form['video_url']
        session_id = str(time.time())
        
        # Start download thread
        threading.Thread(target=download_thread, args=(video_url, session_id)).start()
        
        return '', 202  # Accepted status
    except Exception as e:
        return jsonify(error=str(e)), 500

def download_thread(video_url, session_id):
    # Simulate download process
    time.sleep(5)  # Simulate a 5-second download
    print(f"Download complete for session {session_id}")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
