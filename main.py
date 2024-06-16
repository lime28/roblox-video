from flask import Flask, request
from datetime import datetime
import cv2
from pytube import YouTube
import numpy as np
import json
import logging

app = Flask(__name__)

import ssl

ssl._create_default_https_context = ssl._create_stdlib_context

streams = {}

def time_ago(dt):
    now = datetime.now()
    delta = now - dt
    seconds = delta.total_seconds()
    intervals = (
        ('year', 31536000),  # 60 * 60 * 24 * 365
        ('month', 2592000),  # 60 * 60 * 24 * 30
        ('week', 604800),    # 60 * 60 * 24 * 7
        ('day', 86400),      # 60 * 60 * 24
        ('hour', 3600),      # 60 * 60
        ('minute', 60),
        ('second', 1),
    )
    for name, count in intervals:
        value = seconds // count
        if value:
            return f"{int(value)} {name}{'s' if value > 1 else ''} ago"
    return "just now"
    
def get_stream_url(youtube_url):
    if streams.get(youtube_url):
        return streams[youtube_url][4]
    else:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(res="144p", adaptive=True, mime_type='video/mp4').first()
    
        if stream is None:
            raise ValueError("No suitable stream found for the YouTube video.")
        
        streams[youtube_url] = [
            yt.title,
            yt.views,
            yt.author,
            time_ago(yt.publish_date),
            stream.url
        ]
        return stream.url

def extract_rgb_data(video_url, startFrame, frames, getMeta):

    stream_url = get_stream_url(video_url)
    cap = cv2.VideoCapture(stream_url)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if startFrame > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, startFrame)

    frames_rgb_data = []

    while cap.isOpened() and len(frames_rgb_data) < frames:
        ret, frame = cap.read()
        if not ret:
            break

        resize_frame = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_LANCZOS4)
        rgb_frame = cv2.cvtColor(resize_frame, cv2.COLOR_BGR2RGB)
        flattened = rgb_frame.flatten().tolist()
        # adjusted = np.round(np.array(flattened) / 255.0, 3).tolist()
        frames_rgb_data.append(flattened)

    cap.release()

    metadata = streams[video_url].copy()
    metadata[4] = total_frames

    if getMeta:
        return json.dumps({'metadata': metadata, 'frames': frames_rgb_data})
    else:
        return json.dumps(frames_rgb_data)

@app.route('/get_rgb_data', methods=['POST'])
def get_rgb_data():
    if not request.json or 'video_url' not in request.json:
        return json.dumps({'error': 'Invalid JSON body'}), 400
    
    video_url = request.json['video_url']
    startFrame = request.json['startFrame'] or 0
    frames = request.json['frames'] or 100000000000
    getMeta = request.json['getMeta'] or False

    return extract_rgb_data(video_url, startFrame, frames, getMeta)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host="0.0.0.0", port=8080)
