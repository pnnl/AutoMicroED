# ref. https://superuser.com/questions/726543/how-to-open-raw-file-with-bizarre-custom-header
import matplotlib.cm as cm
import numpy as np
import pylab


#filename = "165749merged_0009_tail_2.img"
filename = "165749merged_0009.img"


#Load the raw file
f_in = open(filename,'rb') # switch to command line args later
#Because the byte order is weird
header = f_in.read(512)
print (f"header:{header}")
#b'{\nHEADER_BYTES=

#rest = f_in.read()
#print (f"rest:{rest}")
#...f\x00\x9a\x00\\\x00'

#rest_encoded = int(rest.encode('hex'), 16)
#AttributeError: 'bytes' object has no attribute 'encode'

#And everything else is 8 bit encoded, so let's load it into numpy and display it with matplotlib
bin_image = np.fromstring(f_in.read(), dtype=np.uint8)

print (f"bin_image.shape:{bin_image.shape}")
#(8388608,)

print (f"len(bin_image):{len(bin_image)}")
#8388608

#Change the shape of the array to the actual shape of the picture
bin_image.shape = (2048, -1)

fig = pylab.figure()
#Display the original image
fig.add_subplot(1,4,1)
pylab.imshow(bin_image, cmap=cm.gray)


