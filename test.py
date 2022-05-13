import os
from PIL import Image
path = os.path.join(os.getcwd(),f"/img/sol.jpg")
print(os.path.exists(path))
image = Image.open(os.getcwd() + path)
image.show()