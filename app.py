import os
import cv2
import shutil
from flask import Flask, render_template, request, send_file, redirect, url_for
from youtube_dl import YoutubeDL

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['FRAME_FOLDER'] = 'frames'

# Ensure folders exist
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAME_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form['video_url']
    
    try:
        # Cleanup previous downloads
        shutil.rmtree(app.config['DOWNLOAD_FOLDER'], ignore_errors=True)
        os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

        # Download video
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], 'video.%(ext)s'),
            'quiet': True  # Suppress youtube-dl logs
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return redirect(url_for('extract_frames'))
    
    except Exception as e:
        return f"Error downloading video: {str(e)}", 500

@app.route('/extract_frames')
def extract_frames():
    try:
        # Cleanup previous frames
        shutil.rmtree(app.config['FRAME_FOLDER'], ignore_errors=True)
        os.makedirs(app.config['FRAME_FOLDER'], exist_ok=True)

        # Find the downloaded video
        video_path = None
        for file in os.listdir(app.config['DOWNLOAD_FOLDER']):
            if file.startswith('video.'):
                video_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file)
                break

        if not video_path:
            return "Video not found!", 404

        # Extract frames
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_path = os.path.join(app.config['FRAME_FOLDER'], f'frame_{frame_count:04d}.jpg')
            cv2.imwrite(frame_path, frame)
            frame_count += 1
        cap.release()

        # Cleanup downloaded video
        os.remove(video_path)

        return redirect(url_for('download_frames'))
    
    except Exception as e:
        return f"Error extracting frames: {str(e)}", 500

@app.route('/download_frames')
def download_frames():
    try:
        # Create ZIP of frames
        shutil.make_archive('frames', 'zip', app.config['FRAME_FOLDER'])
        return send_file('frames.zip', as_attachment=True)
    except Exception as e:
        return f"Error creating ZIP: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses `PORT` env var
    app.run(host='0.0.0.0', port=port, debug=False)
