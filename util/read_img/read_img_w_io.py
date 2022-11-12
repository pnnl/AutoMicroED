import io
#https://stackoverflow.com/questions/38518023/unicodedecodeerror-utf8-codec-cant-decode-byte-0x80-in-position-3131-invali


#Load the raw file
file_name = "165749merged_0009.img"
f = open(file_name,'rb') # switch to command line args later
#f = open(file_name,'r') # switch to command line args later

with io.open(file_name, 'r', encoding='windows-1252') as twitter_file:
    for line in twitter_file:
    	#UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 548: character maps to <undefined>
        # line is now a <type 'unicode'>
        tweet = json.loads(line)



bytes_all = f.read()

#print (f"len(all):{len(all)}")
#8,389,120

#print (f"all.shape:{all.shape}")
#AttributeError: 'bytes' object has no attribute 'shape'

#print (f"all[:100]:{all[:100]}")
#b'{\nHEADER_BYTES=  512;\nBEAM_CENTER_X=57.3440018;\nBEAM_CENTER_Y=57.3440018;\nBIN=2x2;\nBYTE_ORDER=little'

#print (f"all[100:200]:{all[100:200]}")
#b'_endian;\nDATE=Thu Jan  1 00:00:09 1970;\nDETECTOR_SN=unknown;\nDIM=2;\nDISTANCE=759.469971;\nOSC_RANGE=0'

#print (f"all[200:300]:{all[200:300]}")
#b'.600000024;\nOSC_START=4.80000019;\nPHI=4.80000019;\nSIZE1=2048;\nSIZE2=2048;\nIMAGE_PEDESTAL=128;\nPIXEL_'

#print (f"all[300:400]:{all[300:400]}")
#b'SIZE=0.0560000017;\nTIME=1;\nWAVELENGTH=0.0196000002;\nTWOTHETA=0;\nTYPE=unsigned_short;\n}\n

#print (f"all[400:500]:{all[400:500]}")
#b'

#print (f"all[500:600]:{all[500:600]}")
#b'            \x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x8c\x00x\x00\x91\x00\x96\x00\x95\x00|\x00o\x00x\x00\x9b\x00x\x00x\x00p\x00\x8b\x00\x90\x00\x80\x00\x80\x00l\x00\x80\x00x\x00\x98\x00\xa3\x00\x9c\x00\x90\x00\x80\x00k\x00p\x00t\x00x\x00m\x00\x88\x00\x80\x00|\x00c\x00p\x00\x80\x00e\x00x\x00d\x00s\x00'

print (f"bytes_all[512:600]:{bytes_all[512:600]}")
#b'\x80\x00\x80...

import unicodedata

str_512_600 = bytes_all[512:600].decode()

print(unicodedata.normalize('NFKD', str_all[512:600]).encode('ascii', 'ignore'))

a=b
#print (f"all:{all}")
# --> \x80\x00...\x00\\\x00'
# which are UTF (Unicode Transformation Format)-8


#First line is rows
rows = int((b+a).encode('hex'), 16)
a = f.read(1)
b = f.read(1)


'''
#Second line is columns
cols = int((b+a).encode('hex'), 16)
#Last byte is encoding, but we're just going to ignore it
f.read(1)
#And everything else is 8 bit encoded, so let's load it into numpy and display it with matplotlib
bin_image = np.fromstring(f.read(), dtype=np.uint8)
#Change the shape of the array to the actual shape of the picture
bin_image.shape = (cols, rows)

fig = pylab.figure()
#Display the original image
fig.add_subplot(1,4,1)
pylab.imshow(bin_image, cmap=cm.gray)
'''