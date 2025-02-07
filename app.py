import os
import cv2
import shutil
from flask import Flask, render_template, request, send_file, redirect, url_for
from youtube_dl import YoutubeDL

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['FRAME_FOLDER'] = 'frames'

# Ensure download and frame folders exist
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAME_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form['video_url']
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], 'video.%(ext)s'),
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return redirect(url_for('extract_frames'))

@app.route('/extract_frames')
def extract_frames():
    # Clear previous frames
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
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(app.config['FRAME_FOLDER'], f'frame_{frame_count:04d}.jpg')
        cv2.imwrite(frame_path, frame)
        frame_count += 1
    cap.release()

    return redirect(url_for('download_frames'))

@app.route('/download_frames')
def download_frames():
    # Create a ZIP file of all frames
    shutil.make_archive('frames', 'zip', app.config['FRAME_FOLDER'])
    return send_file('frames.zip', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
