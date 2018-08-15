from matplotlib import pyplot as plt
from data_loader import territories


img = plt.imread("map_image.jpg")

y_offset = 10.5

fig, ax = plt.subplots()
ax.imshow(img, extent=[0, 76, 0, 52])
x = [t['x']  for t in territories.values()]
y = [t['y'] + y_offset for t in territories.values()]

plt.plot(x, y, '.')
# for t in territories.values():
#     plt.text(t['x'], t['y'], t['name'], fontsize=5)
plt.show()
