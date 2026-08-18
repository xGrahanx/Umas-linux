from PIL import Image

img = Image.open("gremlins/gold-ship/sprites/sleep.png")
print("Size:", img.size)
print("Mode:", img.mode)

# Check if we can find a clean background pixel to transparentize
# We'll just look at a small section
