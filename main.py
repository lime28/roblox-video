from flask import Flask, request
from datetime import datetime
import cv2
from pytube import YouTube
import numpy as np
import json

app = Flask(__name__)

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

streams = {}

def time_ago(dt):
    now = datetime.now()
    delta = now - dt

    seconds = delta.total_seconds()

    # Define time intervals in seconds
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    week = 7 * day
    month = 30 * day  # Approximation, as months can have different lengths
    year = 365 * day  # Approximation, as years can have leap years

    # Determine the appropriate time unit and amount
    if seconds < minute:
        seconds_ago = int(seconds)
        return f"{seconds_ago} second{'s' if seconds_ago != 1 else ''} ago"
    elif seconds < hour:
        minutes = int(seconds // minute)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < day:
        hours = int(seconds // hour)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < week:
        days = int(seconds // day)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < month:
        weeks = int(seconds // week)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < year:
        months = int(seconds // month)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds // year)
        return f"{years} year{'s' if years != 1 else ''} ago"
    
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


        resize_frame = cv2.resize(frame, (128, 72), interpolation=cv2.INTER_LANCZOS4)

        rgb_frame = cv2.cvtColor(resize_frame, cv2.COLOR_BGR2RGBA)

        flattened = rgb_frame.flatten().tolist()

        adjusted = np.round(np.array(flattened) / 255.0, 3).tolist()

        frames_rgb_data.append(adjusted)

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
    app.run(debug=True, host="0.0.0.0", port=8080)
