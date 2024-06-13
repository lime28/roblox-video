from flask import Flask, request, jsonify
import cv2
from pytube import YouTube

app = Flask(__name__)

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
    
def get_youtube_video_url(youtube_url):
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(res="144p", adaptive=True, mime_type='video/mp4').first()
    
    if stream is None:
        raise ValueError("No suitable stream found for the YouTube video.")
    
    return stream.url

def extract_rgb_data(youtube_url):

    video_url = get_youtube_video_url(youtube_url)
    cap = cv2.VideoCapture(video_url)

    frames_rgb_data = []

    while cap.isOpened() and len(frames_rgb_data) < 256*144*3 * 1:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Flatten the frame to a list of RGB values
        flattened_rgb_data = rgb_frame.flatten().tolist()
        frames_rgb_data.extend(flattened_rgb_data)
        print(len(frames_rgb_data))

    cap.release()

    frames_rgb_data_str = '[' + ','.join(map(str, frames_rgb_data)) + ']'
    return frames_rgb_data_str

@app.route('/get_rgb_data', methods=['POST'])
def get_rgb_data():
    if not request.json or 'video_url' not in request.json:
        return jsonify({'error': 'Invalid JSON body'}), 400
    
    video_url = request.json['video_url']

    return extract_rgb_data(video_url)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
