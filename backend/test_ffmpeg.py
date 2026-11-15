import subprocess

subprocess.run([
    "ffmpeg",
    "-i",
    "uploads/preply.mp4",
    "-c:v",
    "libx264",
    "-c:a",
    "aac",
    "uploads/python_output.mp4"
])