import codecs, io
import unicodedata

#ref. https://superuser.com/questions/726543/how-to-open-raw-file-with-bizarre-custom-header

#Load the raw file
path = "165749merged_0009.img"

#f = open(filename,'rb') # switch to command line args later

with open(path, 'rb') as f_in:
	#bytes_text = f_in.read()
	#print (f"type(bytes_text):{type(bytes_text)}")
	#<class 'bytes'>

	#print (f"bytes_text:{bytes_text}")
	#\xad\x00...
	
	#with io.open("bytes_text.txt",'w',encoding='utf8') as f_out:
	#	f_out.write(bytes_text)
		#TypeError: write() argument must be str, not bytes

	#rows = int((bytes_text).encode('hex'), 16)
	#AttributeError: 'bytes' object has no attribute 'encode'

	str_text = f_in.read().decode(errors='replace')
	#print (f"type(str_text):{type(str_text)}")
	#<class 'str'>

	#print (f"str_text:{str_text}")

	with io.open("str_text.txt",'w',encoding='utf8') as f_out:
		f_out.write(str_text)

	
	#yq�����Mx|
	
	#rows = int((str_text).encode('hex'), 16)
	#LookupError: 'hex' is not a text encoding; use codecs.encode() to handle arbitrary codecs

	#str_512_600_encoded = codecs.encode(str_text[512:600])
	#print (f"str_512_600_encoded:{str_512_600_encoded}")
	#b'\xef\xbf

	#with io.open("unicode.txt",'w',encoding='utf8') as f_out:
	#	f_out.write(str_512_600_encoded)
		#TypeError: write() argument must be str, not bytes

	#print(type(unicodedata.normalize('NFKD', str_text).encode('ascii', 'ignore')))
	#<class 'bytes'>

	#print(unicodedata.normalize('NFKD', str_text).encode('ascii', 'ignore'))
	#\x00o\x00y...
	a=b

#Because the byte order is weird
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



#str_512_600 = bytes_all[512:600].decode()

#str_512_600 = str(bytes_all[512:600], 'UTF-8')
#UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte

str_512_600 = codecs.decode(bytes_all[512:600])
#UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte

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