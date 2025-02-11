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
