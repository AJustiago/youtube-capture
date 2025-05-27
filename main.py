import streamlit as st
import cv2
import tempfile
import os
from PIL import Image
import zipfile
import io
import subprocess


temp_file = "downloaded_video.mp4"

def download_youtube_video(url):
    try:
        cmd = [
            "yt-dlp",
            url,
            "-o", "downloaded_video.mp4"
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        return temp_file

    except Exception as e:
        st.error(f"An error occurred during download: {e}")
        raise


def capture_frames(video_path, interval_sec=8):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    frame_count = 0
    success = True

    while success:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        success, frame = cap.read()
        if success:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            timestamp = round(frame_count / fps, 2)
            frames.append((timestamp, img))
            frame_count += int(fps * interval_sec)
    cap.release()
    return frames

def save_frames_to_zip(frames):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for timestamp, img in frames:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            zip_file.writestr(f"frame_{timestamp:.2f}s.png", img_bytes.getvalue())
    zip_buffer.seek(0)
    return zip_buffer

# --- Streamlit UI ---
st.title("Capture YouTube Video Frames as ZIP")

video_url = st.text_input("Enter YouTube video URL")
run_button = st.button("Run")
interval_sec = st.slider("Frame capture interval (seconds)", min_value=1, max_value=60, value=8)

if run_button and video_url:
    with st.spinner("Downloading and processing video..."):
        try:
            video_file = download_youtube_video(video_url)
            frames = capture_frames(video_file, interval_sec=interval_sec)
            st.success(f"Captured {len(frames)} frames")

            # Display first 3 frames as preview
            for i, (timestamp, img) in enumerate(frames[:3]):
                st.image(img, caption=f"Preview Frame at {timestamp}s")

            # Save to zip
            zip_file = save_frames_to_zip(frames)

            # Download button
            st.download_button(
                label="📦 Download ZIP of Frames",
                data=zip_file,
                file_name="youtube_frames.zip",
                mime="application/zip"
            )

            os.remove(video_file) 
        except Exception as e:
            st.error(f"Error: {e}")
