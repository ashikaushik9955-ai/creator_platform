
from pathlib import Path

from app.services.video_processor import generate_video_version

input_path = Path("uploads/preply.mp4")
output_path = Path("uploads/low_test.mp4")

result = generate_video_version(
    input_path=input_path,
    output_path=output_path,
    quality="high",
)

print("Generated video:", result)
print("File exists:", result.exists())
print("File size (MB):", round(result.stat().st_size / (1024 * 1024), 2))
