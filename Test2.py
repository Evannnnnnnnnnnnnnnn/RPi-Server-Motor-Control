print("\033cStart")

import math

angle = math.radians(60)
forearm = 20
arm = 50

cable = math.sin(angle)*(forearm/math.sin(math.atan(forearm/arm)))

print(cable)










print("End")