import os
import cv2
import shutil
import threading
import time
from flask import Flask, render_template, request, send_file, redirect, url_for, Response
from yt_dlp import YoutubeDL

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['FRAME_FOLDER'] = 'frames'
app.config['SECRET_KEY'] = 'your-secret-key'

# For progress updates
current_progress = {}
progress_lock = threading.Lock()

# ======================
# Progress Hook Function
# ======================
def progress_hook(d, session_id):
    if d['status'] == 'downloading':
        with progress_lock:
            current_progress[session_id] = {
                'percentage': d.get('_percent_str', '0%'),
                'speed': d.get('_speed_str', 'N/A'),
                'eta': d.get('_eta_str', 'N/A')
            }
    elif d['status'] == 'finished':
        with progress_lock:
            current_progress[session_id] = {'percentage': '100%', 'status': 'Processing...'}

# ======================
# Route Handlers
# ======================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    session_id = str(time.time())  # Unique session ID
    video_url = request.form['video_url']
    
    # Start download in separate thread
    threading.Thread(target=download_thread, args=(video_url, session_id)).start()
    
    return redirect(url_for('download_status', session_id=session_id))

@app.route('/status/<session_id>')
def download_status(session_id):
    def generate():
        while True:
            with progress_lock:
                progress = current_progress.get(session_id, {})
            yield f"data: {progress}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

# ======================
# Core Functions
# ======================
def download_thread(video_url, session_id):
    try:
        # Platform-specific configuration
        ydl_opts = get_platform_config(video_url, session_id)
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Trigger frame extraction
        extract_frames(session_id)
        
    except Exception as e:
        with progress_lock:
            current_progress[session_id] = {'error': str(e)}

def get_platform_config(video_url, session_id):
    config = {
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], 'video.%(ext)s'),
        'progress_hooks': [lambda d: progress_hook(d, session_id)],
        'quiet': True,
        'noplaylist': True,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'referer': get_referer(video_url),
        'cookiefile': 'cookies.txt'  # Add cookies if needed
    }
    
    if 'instagram.com' in video_url:
        config.update({'format': 'bestvideo+bestaudio/best'})
    elif 'tiktok.com' in video_url:
        config.update({'format': 'mp4'})
    
    return config

def get_referer(url):
    if 'youtube.com' in url: return 'https://www.youtube.com/'
    if 'tiktok.com' in url: return 'https://www.tiktok.com/'
    if 'instagram.com' in url: return 'https://www.instagram.com/'
    return url

def extract_frames(session_id):
    try:
        # Frame extraction logic
        video_path = get_downloaded_video()
        cap = cv2.VideoCapture(video_path)
        
        with progress_lock:
            current_progress[session_id] = {'status': 'Extracting frames...'}
            
        # Your frame extraction code here
        
        with progress_lock:
            current_progress[session_id] = {'status': 'ready_for_download'}
            
    except Exception as e:
        with progress_lock:
            current_progress[session_id] = {'error': str(e)}

# ======================
# Run Application
# ======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
