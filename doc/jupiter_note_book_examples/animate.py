import numpy as np
from PIL import Image

img = Image.open(r"C:\Users\rmagala\Downloads\IMG_1083.jpg")      # load image
arr = np.array(img)                # convert to NumPy array

print(arr.shape)                   # (H, W, C) or (H, W)
