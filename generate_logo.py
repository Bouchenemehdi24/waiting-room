from PIL import Image, ImageDraw, ImageFont
import os

# Ensure assets directory exists
os.makedirs("assets", exist_ok=True)

# Create a blank image with white background
width, height = 200, 200
image = Image.new("RGBA", (width, height), "white")
draw = ImageDraw.Draw(image)

# Draw a simple blue circle as the logo
circle_radius = 80
circle_center = (width // 2, height // 2)
draw.ellipse(
    [
        (circle_center[0] - circle_radius, circle_center[1] - circle_radius),
        (circle_center[0] + circle_radius, circle_center[1] + circle_radius),
    ],
    fill="#3498db",
    outline="black",
    width=4,
)

# Add app name text in the center
try:
    font = ImageFont.truetype("arial.ttf", 32)
except IOError:
    font = ImageFont.load_default()

text = "App"
text_width, text_height = draw.textsize(text, font=font)
text_position = (circle_center[0] - text_width // 2, circle_center[1] - text_height // 2)
draw.text(text_position, text, fill="white", font=font)

# Save the logo
logo_path = os.path.join("assets", "logo.png")
image.save(logo_path)
print(f"Logo saved to {logo_path}")