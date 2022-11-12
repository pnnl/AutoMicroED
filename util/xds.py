import codecs, glob, math, os, random, shutil, subprocess, sys, time
from datetime import datetime as dt
import matplotlib.image as mpimg
import mrcfile
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter
import util

home_dir_path = os.path.expanduser("~")

## <begin> writing print_this_for_ORGXY
print_this = "\n\t(note) A user may locate ORGX and ORGY by opening *.img or *.mrc files by Adxv."
print_this = print_this + "\n\t(macOS) Adxv can be installed in /Applications"

print_this = print_this + "\n\t(after ssh at linux machine) cd /opt/apps/bin (and) ./adxv.x86_64CentOS7 (enter to launch adxv)"
print_this = print_this + "\n\t\t(when ssh to linux machine by iterm2) In order to open Adxv in user's computer rather than krios GPU machine itself, a user needs to ssh with either -X or -Y. ssh with -XC doesn't work"
print_this = print_this + "\n\t\t(when ssh to linux machine by iterm2) For example, ssh -X kimd999@kriosgpu.emsl.pnl.gov works. However, ssh -XC kimd999@kriosgpu.emsl.pnl.gov doesn't work"
print_this = print_this + "\n\t\t(when ssh to linux machine by x11-x-term) In order to open Adxv in user's computer rather than krios GPU machine itself, a user needs to ssh with -Y only. ssh with -XC or -X don't work"
print_this = print_this + "\n\t\t(when ssh to linux machine by x11-x-term) For example, ssh -Y kimd999@kriosgpu.emsl.pnl.gov works."
print_this = print_this + "\n\t These result image files (*.img) are in output/<date-time of this job>/<mrc file list prefix>/img"
print_this = print_this + "\n\t (note) Example cross is in empiar-10293_adxv.png in reference folder."
print_this = print_this + "\n\t\t(reference) https://strucbio.biologie.uni-konstanz.de/xdswiki/index.php/Finding_out_ORGX_ORGY)"
print_this = print_this + "\n\t\t The error you make in the determination of ORGX ORGY should in principle be less than half of the distance between two spots."
print_this = print_this + "\n\t\t If you have a reasonable estimate (from one of the methods above), but the error is bigger than that, you can still find out the true ORGX ORGY by inspecting IDXREF.LP."
print_this = print_this + "\n\t\t This works best if COLSPOT has seen a significant fraction of all frames. This procedure is documented."
print_this_for_ORGXY = print_this + "\n\t\t (note) At least with Doo Nam's experience, finding true ORGX ORGY by inspecting IDXREF.LP was not feasible."
## <end> writing print_this_for_ORGXY


def add_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict):
  BEAM_DIVERGENCE, REFLECTING_RANGE = get_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
  if (BEAM_DIVERGENCE == None):
    write_this = "BEAM_DIVERGENCE=None, exit now\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    return False
  
  util.flog("AutoMicroED will add BEAM_DIVERGENCE and REFLECTING_RANGE to XDS.INP\n", args_dict['logfile_name_w_abs_path'])
  f_in  = codecs.open("XDS.INP", 'r')
  new_XDS_INP_file_name = "XDS_w_BEAM.INP" ## so that XDS_default can add BEAM_DIVERGENCE
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    f_out.write(line)
  f_in.close()
  
  today = dt.now()
  time_now = today.strftime('%Y/%m/%d') + "/" + str(today.hour) + ":" + str(today.minute) + ":" + str(today.second)
  
  write_this = "\n! " + str(time_now) + "\n"
  f_out.write(write_this)

  write_this = "BEAM_DIVERGENCE=" + str(BEAM_DIVERGENCE) + "\n"
  f_out.write(write_this)
  
  write_this = "REFLECTING_RANGE=" + str(REFLECTING_RANGE) + "\n"
  f_out.write(write_this)

  f_out.close()
  
  shutil.move("XDS_w_BEAM.INP", "XDS.INP")
############# end of def add_BEAM_DIVERGENCE_REFLECTING_RANGE()


def add_DELPHI_10(logfile_name_w_abs_path):
  util.flog("This will add DELPHI=10.\n", logfile_name_w_abs_path)
  util.flog("(DELPHI parameter controls the number of spot profiles for integration. This parameter can be increased from its default value of 5 degree if there are too few spots to establish adequate profiles.)\n", logfile_name_w_abs_path)
  
  f_in  = codecs.open("XDS.INP", 'r')
  new_XDS_INP_file_name = "XDS_w_DELPHI_10.INP" ## so that XDS_default can add BEAM_DIVERGENCE
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    f_out.write(line)
  f_in.close()
  f_out.write("DELPHI=10\n")
  f_out.close()
  
  shutil.move("XDS_w_DELPHI_10.INP", "XDS.INP")
############# end of def add_DELPHI_10()


def estimate_ORGXY_by_beamstop(args_dict, ORGX_ORGY, pixel_in_2D):
  half = int(args_dict['NX'])/2   # 1024.0

  lower_limit = half*0.95 
  upper_limit = half*1.05 

  df = pd.DataFrame(columns=['x', 'y', 'pixel'])
  df_mrc_data = pd.DataFrame(pixel_in_2D)
  for x in range(len(pixel_in_2D)):
    if (x < lower_limit) or (x > upper_limit):
      continue
    for y in range(len(pixel_in_2D[0])): 
      if (y < lower_limit) or (y > upper_limit):
        continue
      
      pixel = return_pixel_including_neighbors(df_mrc_data, x, y, 100)

      # estimation with 25 neighbor (df): 1057.1/1019 (82=38+44) took 36 sec
      # estimation with 40 neighbor (df): 1051/1019 (=+44) took 37 sec
      # estimation with 50 neighbor (df): 1049.1/1023.0 (78=30+48) took 38 sec
      # estimation with 100 neighbor (df): 1061/1060.0 (134=49+85) took 42 sec
      # estimation with 500 neighbor (df): 987.25/1061 took 1.7 min


      df_to_add = pd.DataFrame({"x":[x],
                                "y":[y],
                                "pixel":[pixel]})
      df = df.append(df_to_add, ignore_index=True)

  df_sorted = df.sort_values(by=['pixel'])
  #print (f"df_sorted:{df_sorted}")
  # -> lower values (61540, black) come first
  # -> higher values (95867, white) come later

  #print (df_sorted.shape)
  # for /gpustorage/MicroEDProc/SMP/carb030221/2021-03-02-152943/152943merged.mrcs 
  #-> (23409, 3)
  
  

  #df_top_candidate = df_sorted[:20]
  #-> resulted in 1048.3 x 1019.0

  #df_top_candidate = df_sorted[:100]
  # -> resulted in 1048.05 x 1018.9

  df_top_candidate = df_sorted[:5000]

  # half -> 1024 x 1024 
  # old way -> 1058 x 1023
  # new way -> 1048.3 x 1019.0

  ORGX = df_top_candidate['x'].mean()
  ORGY = df_top_candidate['y'].mean()

  ORGX = round(ORGX, 1)
  print (f"(before averaging) ORGX:{ORGX}") # 1050

  ORGY = round(ORGY, 1)
  print (f"(before averaging) ORGY:{ORGY}") # 1024


  #1024 x 1024 has nothing to do with true orgxy

  if (ORGX_ORGY == "ORGX"):
    print (f"ORGX:{ORGX}")
    return ORGX
  else:
    print (f"ORGY:{ORGY}")
    return ORGY
############ end of def estimate_ORGXY_by_beamstop(ORGX_ORGY, mrc_or_mrcs_w_path, logfile_name_w_abs_path):



# def return_pixel_including_neighbors(df_mrc_data, x, y, pad):
#   summed_pixel = df_mrc_data.iloc[x-pad:x+pad, y-pad:y+pad].sum()
#   pixel = np.mean(summed_pixel)
#   pixel = round(pixel, 2)
#   return pixel
# # end of def return_pixel_including_neighbors(img, x, y):


def return_pixel_including_neighbors_wo_df(pixel_in_2D, x, y, pad):
  pixels_w_neighbor = pixel_in_2D[x-pad:x+pad, y-pad:y+pad]
  #np.savetxt("pixel_in_2D_part.csv", pixels_w_neighbor, delimiter=',')
  
  pixel_w_neighbor = np.mean(pixels_w_neighbor)

  return round(float(pixel_w_neighbor),2)
# end of def return_pixel_including_neighbors_wo_df(pixel_in_2D):


'''
def estimate_ORGXY_by_center_circle_radially(args_dict, ORGX_ORGY, pixel_in_2D):
  #print (f"type(pixel_in_2D):{type(pixel_in_2D)}")
  #<class 'numpy.memmap'>


  csv_filename = 'pixel_in_2D_raw.csv'
  np.savetxt(csv_filename, pixel_in_2D[824:1224, 824:1224], delimiter=',')


  half = int(int(args_dict['NX'])/2)   # 1024

  # pixel_in_2D = pixel_in_2D[int(half*0.80):int(half*1.20), int(half*0.80):int(half*1.20)]




  ######### <begin> blur
  # the higher sigma, the more blurred/exaggerated
  sigma = 5
  
  pixel_in_2D = gaussian_filter(pixel_in_2D, sigma=sigma)

  #png_filename = 'pixel_in_2D_sigma_' + str(sigma) + '.png'
  #mpimg.imsave(png_filename, pixel_in_2D)
  
  #print (f"type(pixel_in_2D):{type(pixel_in_2D)}")
  #<class 'numpy.ndarray'>

  #csv_filename = png_filename[:-4] + ".csv"
  #np.savetxt(csv_filename, pixel_in_2D[824:1224, 824:1224], delimiter=',')


  mean_ = round(float(np.mean(pixel_in_2D)),2)
  print (f"np.mean(pixel_in_2D):{mean_}")  #20.84
  
  std_ = round(float(np.std(pixel_in_2D)),2)
  print (f"np.std(pixel_in_2D):{std_}") # 81.9
  
  ######### <end> blur

  
  #print (f"pixel_in_2D.shape:{pixel_in_2D.shape}")
  #(2048, 2048)

  
  #print (f"pixel_in_2D[half,half]:{pixel_in_2D[half,half]}") # darkest, 16.0
  #print (f"pixel_in_2D[775, 974]:{pixel_in_2D[775, 974]}") # gray, 73.0
  #print (f"pixel_in_2D[1031,1078]:{pixel_in_2D[1031,1078]}") # brightest, 118.0
  #-> the brighter -> larger pixel value
  
  #goal: find pixel variance region that decreases (e.g. toward darker)
  radial_distance_max = int(int(args_dict['NX'])/4)   # 512
  radial_distance_increment = int(int(args_dict['NX'])/400)   # 5
  print (f"radial_distance_increment:{radial_distance_increment}")

  ## <begin> find brighter (higher pixel value) region (e.g. find variances that are significantly negative)
  threshold_variance = -10
  padding = 5

  pixel_center = round(return_pixel_including_neighbors_wo_df(pixel_in_2D, half, half, padding),2)
  print (f"pixel_center:{pixel_center}") # sigma=5 -> 109.43

  #North
  for radial_distance in range(0, radial_distance_max, radial_distance_increment):
    print (f"\nnew x, y:{half},{half+radial_distance}")

    pixel_new      = round((return_pixel_including_neighbors_wo_df(pixel_in_2D, half, half+radial_distance, padding)),2)
    print (f"pixel_new:{pixel_new}")
    
    variance_in_North = round((pixel_center - pixel_new),2)
    print (f"variance_in_North:{variance_in_North}")

    if (variance_in_North < threshold_variance): # using var < -30 results too many
      radial_distance_when_var_negative_N = radial_distance
      print (f"radial_distance_when_var_negative_N:{radial_distance_when_var_negative_N}") # 10 
      break


  
  #South
  for radial_distance in range(0, radial_distance_max, radial_distance_increment):
    print (f"\nnew x, y:{half},{half-radial_distance}")

    pixel_new      = round(return_pixel_including_neighbors_wo_df(pixel_in_2D, half, half-radial_distance, padding),2)
    print (f"pixel_new:{pixel_new}")

    variance_in_South = round((pixel_center - pixel_new),2)
    if (variance_in_South < threshold_variance):

      print (f"variance_in_South:{variance_in_South}")
      radial_distance_when_var_negative_S = radial_distance
      
      break

  #West
  for radial_distance in range(0, radial_distance_max, radial_distance_increment):
    variance_in_West = pixel_in_2D[half, half] - pixel_in_2D[half-radial_distance, half]
    if (variance_in_West < threshold_variance):
      print (f"\nnew x, y:{half-radial_distance},{half}")
      
      print (f"pixel_in_2D[half, half]:{pixel_in_2D[half, half]}")
      print (f"pixel_in_2D[half-radial_distance, half]:{pixel_in_2D[half-radial_distance, half]}")
      print (f"variance_in_West:{variance_in_West}")

      radial_distance_when_var_negative_W = radial_distance
      print (f"radial_distance_when_var_negative_W:{radial_distance_when_var_negative_W}") # 5
      break
    
  ## <end> find brighter region (e.g. find all variances are negative)


############ end of def estimate_ORGXY_by_center_circle_radially(ORGX_ORGY, mrc_or_mrcs_w_path, logfile_name_w_abs_path):
'''


def estimate_ORGXY_by_middle_circle(args_dict, ORGX_ORGY, pixel_in_2D):
  print (f"pixel_in_2D.shape:{pixel_in_2D.shape}")
  #smv itself -> (2048, 4096)
  #print (f"type(pixel_in_2D):{type(pixel_in_2D)}")
  #<class 'numpy.memmap'>


  #csv_filename = 'pixel_in_2D_raw.csv'
  #np.savetxt(csv_filename, pixel_in_2D[824:1224, 824:1224], delimiter=',')



  ######### <begin> blur
  # the higher sigma, the more blurred/exaggerated
  sigma = 5
  
  pixel_in_2D = gaussian_filter(pixel_in_2D, sigma=sigma)

  #png_filename = 'pixel_in_2D_sigma_' + str(sigma) + '.png'
  #mpimg.imsave(png_filename, pixel_in_2D)
  
  #print (f"type(pixel_in_2D):{type(pixel_in_2D)}")
  #<class 'numpy.ndarray'>

  #csv_filename = png_filename[:-4] + ".csv"
  #np.savetxt(csv_filename, pixel_in_2D[824:1224, 824:1224], delimiter=',')


  mean_ = round(float(np.mean(pixel_in_2D)),2)
  print (f"np.mean(pixel_in_2D):{mean_}")  #20.84
  
  std_ = float(np.std(pixel_in_2D))
  print (f"np.std(pixel_in_2D):{round(std_,2)}") # 81.9
  
  print (f"np.max(pixel_in_2D):{round(float(np.max(pixel_in_2D)),2)}")
  print (f"np.min(pixel_in_2D):{round(float(np.min(pixel_in_2D)),2)}")

  print (f"np.median(pixel_in_2D):{round(float(np.median(pixel_in_2D)),2)}")

  ######### <end> blur


  # for mrc (after sigma=5 gaussian)
  # max: 8370
  # min: -25
  # mean: 17
  # median: 3.59
  # std:  89
  # cutoff = round((mean_ + (std_*7)),2) -> 642

  # for smv then png (after sigma=5 gaussian)
  # max: 0.95
  # min: 0
  # mean: 0.89
  # median: 0.91
  # std: 0.08
  # cutoff = round((mean_ + (std_*7)),2) -> 1.45

  # for smv itself (after sigma=5 gaussian)
  # max: 104
  # min: 29
  # mean: 63
  # median: 62
  # std: 8.78
  # cutoff = 

  if (args_dict["file_format_for_ORGXY"] == "mrc"):
    cutoff = round((mean_ + (std_*6)),2)
  elif (args_dict["file_format_for_ORGXY"] == "smv_then_png"):
    cutoff = round((mean_ - std_*6),2)
  else: # (args_dict["file_format_for_ORGXY"] == "smv_itself"):
    cutoff = round((mean_ + std_*3),2)
    #cutoff = round((mean_ + std_*2),2)
    #cutoff = round((mean_ + std_*3),2) -> It leaves relavant part better, but results in ORGY=nan sometimes


  #print (f"type(cutoff):{type(cutoff)}") #<class 'float'>
  print (f"cutoff:{cutoff}") # 986.93

  # original
  #pixel_in_2D_cut = np.where(pixel_in_2D > cutoff, pixel_in_2D, 0)

  # more effective binary mask
  if (args_dict["file_format_for_ORGXY"] == "mrc"):
    pixel_in_2D_cut = np.where(pixel_in_2D > float(cutoff), 1000, 0)
    csv_filename = 'pixel_in_2D_brighter_than_' + str(cutoff) + '.csv'

  elif (args_dict["file_format_for_ORGXY"] == "smv_then_png"):
    pixel_in_2D_cut = np.where(pixel_in_2D < float(cutoff), 1000, 0)
    csv_filename = 'pixel_in_2D_darker_than_' + str(cutoff) + '.csv'

  else: # (args_dict["file_format_for_ORGXY"] == "smv_itself"):
    pixel_in_2D_cut = np.where(pixel_in_2D > float(cutoff), 1000, 0)
    csv_filename = 'pixel_in_2D_brighter_than_' + str(cutoff) + '.csv'
  
  
  #np.savetxt(csv_filename, pixel_in_2D_cut, delimiter=',')

  png_filename = csv_filename[:-4] + '.png'


  #print (f"pixel_in_2D_cut:{pixel_in_2D_cut}")
  print (f"pixel_in_2D_cut.shape:{pixel_in_2D_cut.shape}")
  #(2048, 2048, 1)


  mpimg.imsave(png_filename, pixel_in_2D_cut)

  arr_ij = np.argwhere(pixel_in_2D_cut!=0)


  #arr_ij = np.where(arr_ij < (half*0.8), np.nan, arr_ij)
  #arr_ij = np.where(arr_ij > (half*1.2), np.nan, arr_ij)
  # 20% -> 948, 1180

  

  #arr_ij = np.where(arr_ij < (half*0.5), np.nan, arr_ij)
  #arr_ij = np.where(arr_ij > (half*1.5), np.nan, arr_ij)
  #-> it leads to ORGY=1486.49
  
  #print (f"arr_ij.shape:{arr_ij.shape}")
  #(246098, 2)

  #np.savetxt("arr_ij.csv", arr_ij, delimiter=',')
  

  if ORGX_ORGY == "ORGX":
    half = int(int(pixel_in_2D.shape[0])/2)   # 1024
    arr_ij = np.where(arr_ij < (half*0.75), np.nan, arr_ij)
    arr_ij = np.where(arr_ij > (half*1.25), np.nan, arr_ij)
    #25% -> 951.73, 1098

    ORGX = np.nanmean(arr_ij[:,0])
    ORGX = ORGX - int(int(args_dict['NX'])*0.03)
    ORGX = round(ORGX,2)
    print (f"(before averaging) ORGX:{ORGX}")
    if (math.isnan(ORGX) == True):
      print_this = "ORGX is nan"
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
      return -999
    return ORGX
  else:
    half = int(int(pixel_in_2D.shape[1])/2)
    arr_ij = np.where(arr_ij < (half*0.75), np.nan, arr_ij)
    arr_ij = np.where(arr_ij > (half*1.25), np.nan, arr_ij)
    #25% -> 951.73, 1098

    ORGY = np.nanmean(arr_ij[:,1])
      
    ORGY = round(ORGY,2)
    print (f"(before averaging) ORGY:{ORGY}")
    if (math.isnan(ORGY) == True):
      print_this = "ORGY is nan"
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
      return -999
    return ORGY
############ end of def estimate_ORGXY_by_middle_circle(ORGX_ORGY, mrc_or_mrcs_w_path, logfile_name_w_abs_path):


def estimate_ORGXY_for_smv_itself(args_dict, ORGXY, input_smv_file):
  
  f_in = open(input_smv_file,'rb') 
  header = f_in.read(512)

  #f_in = open(input_smv_file,'r') 
  #header = f_in.read(512)
  #UnicodeDecodeError: 'utf-8' codec can't decode byte 0x84 in position 512: invalid start byte

  print (f"header:{header}")

  #index_SIZE1 = header.index("SIZE1")
  #TypeError: argument should be integer or bytes-like object, not 'str'

  


  index_SIZE1 = header.index(b"SIZE1")
  #print (f"index_SIZE1:{index_SIZE1}")

  index_SIZE2 = header.index(b";\nSIZE2")
  #print (f"index_SIZE2:{index_SIZE2}")

  SIZE1 = header[(index_SIZE1+6):(index_SIZE2)].decode()
  print (f"SIZE1:{SIZE1}")
  

  index_IMAGE_PEDESTAL = header.index(b";\nIMAGE_PEDESTAL")
  #print (f"index_IMAGE_PEDESTAL:{index_IMAGE_PEDESTAL}")

  SIZE2 = header[(index_SIZE2+8):(index_IMAGE_PEDESTAL)].decode()
  print (f"SIZE2:{SIZE2}")

  
  args_dict['NX'] = int(SIZE1)
  args_dict['NY'] = int(SIZE2)

  bin_image = np.fromstring(f_in.read(), dtype=np.uint8)
  #bin_image = np.fromstring(f_in.read(), dtype=np.uint16)

  print (f"bin_image.shape:{bin_image.shape}")
  #(8388608,)

  #print (f"len(bin_image):{len(bin_image)}")

  #bin_image.shape = (int(args_dict['NX']), int(args_dict['NY']), -1)
  bin_image.shape = (int(SIZE1), int(SIZE2), -1)


  if (bin_image.shape[2] == 1):
    print ("reading with dtype=np.uint8 is ok")
    pass

  elif (bin_image.shape[2] == 2):
    f_in.close()
    f_in = open(input_smv_file,'rb') 
    header = f_in.read(512)
    bin_image = np.fromstring(f_in.read(), dtype=np.uint16)
    bin_image.shape = (int(SIZE1), int(SIZE2), -1)

  elif (bin_image.shape[2] == 4):
    f_in.close()
    f_in = open(input_smv_file,'rb') 
    header = f_in.read(512)
    bin_image = np.fromstring(f_in.read(), dtype=np.uint32)
    bin_image.shape = (int(SIZE1), int(SIZE2), -1)

  elif (bin_image.shape[2] == 8):
    f_in.close()
    f_in = open(input_smv_file,'rb') 
    header = f_in.read(512)
    bin_image = np.fromstring(f_in.read(), dtype=np.uint64)
    bin_image.shape = (int(SIZE1), int(SIZE2), -1)

  # print (f"bin_image.shape:{bin_image.shape}")
  # print (f"type(bin_image):{type(bin_image)}")
  #<class 'numpy.ndarray'>

  bin_image = np.squeeze(bin_image)
  print (f"bin_image.shape:{bin_image.shape}")
  

  return estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), bin_image)
#### end of def estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), input_smv_file)    


def estimate_ORGXY_for_smv_then_png(args_dict, ORGXY, input_smv_file):
  # 6/30/2022, James mentioned that he will share how to read smv file
  # but the link in https://strucbio.biologie.uni-konstanz.de/ccp4wiki/index.php/SMV_file_format is broken.
  output_png_file = input_smv_file[:-4] + ".png"
  try:
    path = subprocess.check_output(["which", "convert"]).decode('UTF-8')
    #print_this = "\tPath of convert:" + str(path)
    #util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    cmd = "convert "
  except:
    print_this = "\nconvert is not located."
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])

    if ('convert_folder' in args_dict.keys()):
      cmd = str(os.path.join(str(args_dict['convert_folder']), 'convert'))
    else:
      print_this = print_this + "\nDo one of below 3 solutions."
      print_this = print_this + "\n\tSolution #1) Add imagemagick's convert into user's PATH."
      print_this = print_this + "\n\tSolution #2) Refer https://github.com/pnnl/AutoMicroED/blob/master/reference/install_convert.md"
      print_this = print_this + "\n\tSolution #3) Specify convert_folder in user_args_file"

      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
      exit(1)

  cmd = cmd + " -depth 16 -type Grayscale -colorspace GRAY -endian LSB -size 2048x2048+512 GRAY:" + str(input_smv_file) + " -negate -normalize " + str(output_png_file)
  util.flog(cmd, args_dict['logfile_name_w_abs_path'])
  os.system(cmd)

  img = mpimg.imread(output_png_file)
  return estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), img)
#### end of def estimate_ORGXY_for_smv_then_png(args_dict, str(ORGXY), input_smv_file)    


def get_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict):
  BEAM_DIVERGENCE = BEAM_DIVERGENCE_ESD = REFLECTING_RANGE = REFLECTING_RANGE_ESD = None
  if (os.path.isfile("INTEGRATE.LP") == True):
    BEAM_DIVERGENCE, BEAM_DIVERGENCE_ESD, REFLECTING_RANGE, REFLECTING_RANGE_ESD \
    = get_BEAM_DIVERGENCE_REFLECTING_RANGE_now(args_dict['logfile_name_w_abs_path'], "INTEGRATE.LP")
    if (BEAM_DIVERGENCE == None):
      all_immediate_sub_dir = next(os.walk('../..'))[1]
      for i in range(len(all_immediate_sub_dir)):
        check_this_file = os.path.join("../..", all_immediate_sub_dir[i], "xds", "INTEGRATE.LP")
        util.flog(str(check_this_file), args_dict['logfile_name_w_abs_path'])
        if (os.path.isfile(check_this_file)):
          BEAM_DIVERGENCE, BEAM_DIVERGENCE_ESD, REFLECTING_RANGE, REFLECTING_RANGE_ESD \
          = get_BEAM_DIVERGENCE_REFLECTING_RANGE_now(args_dict['logfile_name_w_abs_path'], check_this_file)
          if (BEAM_DIVERGENCE != None):
            break
  else:
    util.flog("INTEGRATE.LP not found in this directory.", args_dict['logfile_name_w_abs_path']) 
    all_immediate_sub_dir = next(os.walk('../..'))[1]
    for i in range(len(all_immediate_sub_dir)):
      check_this_file = os.path.join("../..", all_immediate_sub_dir[i], "xds", "INTEGRATE.LP")
      util.flog(str(check_this_file), args_dict['logfile_name_w_abs_path'])
      if (os.path.isfile(check_this_file)):
        BEAM_DIVERGENCE, BEAM_DIVERGENCE_ESD, REFLECTING_RANGE, REFLECTING_RANGE_ESD \
        = get_BEAM_DIVERGENCE_REFLECTING_RANGE_now(args_dict, check_this_file)
        if (BEAM_DIVERGENCE != None):
          break
  
  return BEAM_DIVERGENCE, REFLECTING_RANGE
########## end of def get_BEAM_DIVERGENCE_REFLECTING_RANGE():


def get_BEAM_DIVERGENCE_REFLECTING_RANGE_now(args_dict, use_this_file_get_BEAM_DIVERGENCE_REFLECTING_RANGE):
  BEAM_DIVERGENCE = BEAM_DIVERGENCE_ESD = REFLECTING_RANGE = REFLECTING_RANGE_ESD = None
  f_in  = codecs.open(use_this_file_get_BEAM_DIVERGENCE_REFLECTING_RANGE, 'r')
  for line in f_in:
    splited_line = line.split()
    if (line[:17] == " BEAM_DIVERGENCE="):
      BEAM_DIVERGENCE = splited_line[1]
      BEAM_DIVERGENCE_ESD = splited_line[3]
    elif (line[:18] == " REFLECTING_RANGE="):
      REFLECTING_RANGE = splited_line[1]
      REFLECTING_RANGE_ESD = splited_line[3]
  f_in.close()
  return BEAM_DIVERGENCE, BEAM_DIVERGENCE_ESD, REFLECTING_RANGE, REFLECTING_RANGE_ESD
########## end of def get_BEAM_DIVERGENCE_REFLECTING_RANGE_now():


def get_ISa(args_dict, use_this_file_get_ISa):
  command = "cat " + str(use_this_file_get_ISa) + " | grep -A 1 ISa | tail -1 "
  extracted = subprocess.check_output(command, shell=True).decode('utf-8')
  splited_extracted = extracted.split()
  ISa = splited_extracted[2]
  return ISa
########## end of def get_ISa():


def loop_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict, xds_log_filename_wo_ext, xds_kind, \
    xds_log_filename_w_ext_that_generates_CORRECT_LP):
  old_ISa = get_ISa(args_dict, xds_log_filename_w_ext_that_generates_CORRECT_LP)

  
  ### <begin> backup for the very first run with added BEAM_DIVERGENCE_REFLECTING_RANGE
  XDS_INP_backup_filename = "XDS.INP.backup_" + str(0)
  shutil.copyfile("XDS.INP", XDS_INP_backup_filename)

  CORRECT_LP_backup_filename = "CORRECT.LP.backup_" + str(0)
  shutil.copyfile("CORRECT.LP", CORRECT_LP_backup_filename)

  XPARM_backup_filename = "XPARM.XDS.backup_" + str(0)
  shutil.copyfile("XPARM.XDS", XPARM_backup_filename)

  #Each file contains all diffraction parameters necessary for computing the locations of all reflections occurring in the data images.
  #An initial set of parameters is determined by "IDXREF" and saved on file XPARM.XDS. A final set of parameters is computed by "CORRECT" and saved on file GXPARM.XDS.
  if os.path.exists("GXPARM.XDS") == True:
    shutil.copyfile("GXPARM.XDS", "XPARM.XDS")
  ### <end> backup for the very first run with added BEAM_DIVERGENCE_REFLECTING_RANGE


  for BEAM_DIVERGENCE_REFLECTING_RANGE_trial in range(1, 100):
    
    add_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
    
    XDS_INP_backup_filename = "XDS.INP.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial)
    shutil.copyfile("XDS.INP", XDS_INP_backup_filename)

    CORRECT_LP_backup_filename = "CORRECT.LP.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial)
    shutil.copyfile("CORRECT.LP", CORRECT_LP_backup_filename)

    XPARM_backup_filename = "XPARM.XDS.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial)
    shutil.copyfile("XPARM.XDS", XPARM_backup_filename)

    shutil.copyfile("GXPARM.XDS", "XPARM.XDS")

    xds_log_filename_wo_ext = "XDS_BEAM_DIVERGENCE_REFLECTING_RANGE_trial_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial)

    if (args_dict['extra_xds_option'] != ""):
      xds_log_filename_wo_ext = xds_log_filename_wo_ext + "_" + str(args_dict['extra_xds_option'])
    run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)

    use_this_file_get_ISa = xds_log_filename_wo_ext + "_" + str(xds_kind) + ".log"
    ISa = get_ISa(args_dict, use_this_file_get_ISa)

    if (float(ISa) <= float(old_ISa)):

      XDS_INP_backup_filename = "XDS.INP.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial-1)
      CORRECT_LP_backup_filename = "CORRECT.LP.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial-1)
      XPARM_backup_filename = "XPARM.XDS.backup_" + str(BEAM_DIVERGENCE_REFLECTING_RANGE_trial-1)

      print_this = str(XDS_INP_backup_filename) + " results in the highest ISa."
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])

      shutil.copyfile(CORRECT_LP_backup_filename, "CORRECT.LP")
      shutil.copyfile(XDS_INP_backup_filename, "XDS.INP")
      shutil.copyfile(XPARM_backup_filename, "XPARM.XDS")
      shutil.copyfile("XPARM.XDS", "GXPARM.XDS")
      break
    else:
      old_ISa = ISa
####### end of def loop_BEAM_DIVERGENCE_REFLECTING_RANGE():


def remove_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict):
  flog("This will remove BEAM_DIVERGENCE and REFLECTING_RANGE.\n", args_dict['logfile_name_w_abs_path'])
  f_in = codecs.open("XDS.INP", 'r')
  new_XDS_INP_file_name = "XDS_wo_BEAM.INP" ## so that XDS_default can add BEAM_DIVERGENCE
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    if (line[:16] == "BEAM_DIVERGENCE="):
      continue
    elif (line[:23] == "BEAM_DIVERGENCE_E.S.D.="):
      continue
    elif (line[:17] == "REFLECTING_RANGE="):
      continue
    elif (line[:24] == "REFLECTING_RANGE_E.S.D.="):
      continue
    else:
      f_out.write(line)
  f_in.close()
  shutil.move("XDS_wo_BEAM.INP", "XDS.INP")
############# end of def remove_BEAM_DIVERGENCE_REFLECTING_RANGE()


def remove_DELPHI_10(args_dict):
  flog("This will remove DELPHI=10.\n", args_dict['logfile_name_w_abs_path'])
  f_in = codecs.open("XDS.INP", 'r')
  new_XDS_INP_file_name = "XDS_wo_DELPHI_10.INP" ## so that XDS_default can add BEAM_DIVERGENCE
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    if (line[:9] == "DELPHI=10"):
      continue
    else:
      f_out.write(line)
  f_in.close()
  shutil.move("XDS_wo_DELPHI_10.INP", "XDS.INP")
############# end of def remove_DELPHI_10()


def return_pixel_including_neighbors(df_mrc_data, x, y, pad):
  summed_pixel = df_mrc_data.iloc[x-pad:x+pad, y-pad:y+pad].sum()
  pixel = np.mean(summed_pixel)
  pixel = round(pixel, 2)
  return pixel
# end of def return_pixel_including_neighbors(img, x, y):


def run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind):
  if (os.path.isfile("CORRECT.LP") == True):
    return True
  
  xds_log_filename_wo_ext = XDS_default(args_dict, mrc_wo_path, output_folder_name, xds_kind)
  if (os.path.isfile("CORRECT.LP") == True):
    return xds_log_filename_wo_ext

  xds_log_filename_wo_ext = XDS_sliding_SPOT_RANGE(args_dict, output_folder_name, xds_kind)
  if (os.path.isfile("CORRECT.LP") == True):
    return xds_log_filename_wo_ext
  
  xds_log_filename_wo_ext = XDS_half_SPOT_RANGE_and_full_BACKGROUND_RANGE(args_dict, output_folder_name, xds_kind)
  if (os.path.isfile("CORRECT.LP") == True):
    return xds_log_filename_wo_ext
  
  xds_log_filename_wo_ext = XDS_shorter_JOB(args_dict, xds_kind)
  if (os.path.isfile("CORRECT.LP") == True):
    return xds_log_filename_wo_ext

  xds_log_filename_wo_ext = XDS_shorter_DATA_RANGE_shorter_JOB(args_dict, xds_kind)
  if (os.path.isfile("CORRECT.LP") == True):
    return xds_log_filename_wo_ext
  
  # Irina prefers not to use full SPOT_RANGE
########### end of def run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind):

    
def run_xds(args_dict, mrc_or_mrcs_w_path, output_folder_name):
  ###### <begin> just check args_dict to prepare XDS.INP to process each mrc
  # This checking ends at line 968

  process = "Prepare XDS.INP to process " + str(mrc_or_mrcs_w_path)
  util.show_header(process)
  
  if (args_dict['input_list_has_mrc'] == True):
    mrc_wo_path = os.path.basename(mrc_or_mrcs_w_path)
  else:
    #print (f"mrc_or_mrcs_w_path:{mrc_or_mrcs_w_path}")
    mrc_wo_path = mrc_or_mrcs_w_path.split('/')[-2]
    #print (f"mrc_wo_path:{mrc_wo_path}")

  mrc_wo_path_wo_ext = os.path.splitext(mrc_wo_path)[0]
  #print (f"mrc_wo_path_wo_ext:{mrc_wo_path_wo_ext}")
  # when individual mrc is provided -> 2021-06-15-165749_0004

  if (args_dict['input_list_has_mrc'] == True):
    if (int(args_dict['sections']) == 1):
      mrc_wo_path_wo_ext_w_4_question_marks = mrc_wo_path_wo_ext[:-5] + "_????"
    
  os.chdir("../xds")
  
  if ("INCLUDE_RESOLUTION_RANGE" in args_dict):
    INCLUDE_RESOLUTION_RANGE = args_dict['INCLUDE_RESOLUTION_RANGE']
  else:
    args_dict['INCLUDE_RESOLUTION_RANGE'] = "99 0.0"
    
  write_this = "INCLUDE_RESOLUTION_RANGE to use: " + str(args_dict['INCLUDE_RESOLUTION_RANGE'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  

  ##### <begin> assign ORGX/ORGY in XDS.INP
  ORG_list = ["ORGX", "ORGY"]
  for ORGXY in ORG_list:
    if (args_dict['input_list_has_mrc'] == True):
      #args_dict["file_format_for_ORGXY"] = "mrc"
      args_dict["file_format_for_ORGXY"] = "smv_itself"

      if (int(args_dict['sections']) == 1): # individual_mrc
        combi = (ORGXY, str(mrc_wo_path_wo_ext_w_4_question_marks)) # mrc_wo_path has .mrc/.mrcs extension
        #print (f"combi:{combi}") #('ORGX', '2021-06-15-165749_????')
      else: # mrcs, args_dict['sections'] = 539
        combi = (ORGXY, str(mrc_wo_path_wo_ext)) # mrc_wo_path has .mrc/.mrcs extension
        #print (f"combi:{combi}") #('ORGX', '165749merged')
      
      # common for both mrcs and individual mrc input
      if (combi not in args_dict):
        print_this = "(note)  AutoMicroED doesn't see " + str(ORGXY) + " in a user-provided args_file."
        print_this = print_this + "\n\t\t\t\tTherefore, it will estimate " + str(ORGXY) + " by mrclibrary."
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])

        ORGXY_start_time = time.time()
        img_folder = os.path.join(os.path.dirname(os.getcwd()), "img")

        glob_this = os.path.join(img_folder,"*.img")
        list_of_img = glob.glob(glob_this)  

        random_index = random.randint(3, int(len(list_of_img)/3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result1 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result1 == -999):
          exit(1)

        random_index = random.randint(int(len(list_of_img)/3), 2*int(len(list_of_img)/3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result2 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result2 == -999):
          exit(1)

        random_index = random.randint(2*int(len(list_of_img)/3), int(len(list_of_img)-3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result3 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result3 == -999):
          exit(1)

        args_dict[combi] = round(((result1 + result2 + result3)/3),2)

        #if (int(args_dict['sections']) > 1): # mrcs input
          #print (f"mrc_or_mrcs_w_path:{mrc_or_mrcs_w_path}")
          #/gpustorage/MicroEDProc/SMP/combogrid_061521/2021-06-15-165749/165749merged.mrcs

          
        ''' (old) uses mrcs for ORGXY estimation
          print_this = "\tA mrcs file that will be used to estimate " + str(ORGXY) + ": " + str(mrc_or_mrcs_w_path)
          util.flog(print_this, args_dict['logfile_name_w_abs_path'])

          mrcs = util.load_density_file(mrc_or_mrcs_w_path)
          
          
          # Irina prefers to use 3 images and average results
          use_this_mrc_for_ORGXY = random.randint(3, int(int(mrcs.data.shape[0])/3))
          print (f"use_this_mrc_for_ORGXY:{use_this_mrc_for_ORGXY}")

          #print (f"len(mrcs.data):{len(mrcs.data)}") 183
          #print (f"mrcs.data.shape:{mrcs.data.shape}") # (183, 2048, 2048)

          #result1 = estimate_ORGXY_by_center_circle_radially(args_dict, str(ORGXY), mrcs.data[use_this_mrc_for_ORGXY])
          result1 = estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), mrcs.data[use_this_mrc_for_ORGXY])
          #print (f"result1:{result1}") # 1018.8

          use_this_mrc_for_ORGXY = random.randint( int(int(mrcs.data.shape[0])/3), 2*int(int(mrcs.data.shape[0])/3) )
          print (f"use_this_mrc_for_ORGXY:{use_this_mrc_for_ORGXY}")
          result2 = estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), mrcs.data[use_this_mrc_for_ORGXY])

          use_this_mrc_for_ORGXY = random.randint(2*int(int(mrcs.data.shape[0])/3), int(mrcs.data.shape[0])-3)
          print (f"use_this_mrc_for_ORGXY:{use_this_mrc_for_ORGXY}")
          result3 = estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), mrcs.data[use_this_mrc_for_ORGXY])
        
        else: # int(args_dict['sections']) = 1 e.g. individual mrc 
          # (old) use mrc file to estimate ORGXY
          print_this = "\tA mrc file that will be used to estimate " + str(ORGXY) + ": " + str(mrc_or_mrcs_w_path)
          util.flog(print_this, args_dict['logfile_name_w_abs_path'])
          mrc = util.load_density_file(mrc_or_mrcs_w_path)
          #args_dict[combi] = estimate_ORGXY_by_beamstop(args_dict, str(ORGXY), mrc.data)
          args_dict[combi] = estimate_ORGXY_by_middle_circle(args_dict, str(ORGXY), mrc.data)
        '''

        ORGXY_end_time = time.time()
        write_this = util.show_time("Estimation of ORGX_ORGY", ORGXY_start_time, ORGXY_end_time)
        util.flog(write_this, args_dict['logfile_name_w_abs_path'])
        
        print_this = str(ORGXY) + " is estimated by AutoMicroED (e.g. " + str(args_dict[combi]) + ")"
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
         
        print_this = "\t\t(Tip) Enter \"bypass\" and hit enter key if a user wants to add current " + str(ORGXY) \
                   + " in an argument file (so that this automatic estimation of " + str(ORGXY) + " can be bypassed next time when user runs AutoMicroED again).\n"
        print_this = print_this + "\t\t(Tip) Otherwise (a user doesn't want to add this estimated " + str(ORGXY) + " to argumenr file, just hit enter key only.\n"
        if ("kimd999" in home_dir_path):
            util.nonBlockingRawInput(print_this)
        else:
          bypass_can = input(print_this)
          if (bypass_can.rstrip() == "bypass") or (bypass_can.rstrip() == "\"bypass\""):
            f_out = codecs.open("../../../../args_file_generated_by_AutoMicroED.txt", 'a')
            if (int(args_dict['sections']) != 1):
              write_this = str(ORGXY) + " " + str(str(mrc_wo_path_wo_ext)) + " " + str(args_dict[combi]) + " # generated by AutoMicroED\n"
            else:
              write_this = str(ORGXY) + " " + str(str(mrc_wo_path_wo_ext[:-5])) + "_???? " + str(args_dict[combi]) + " # generated by AutoMicroED\n"
            f_out.write(write_this)
            f_out.close()
      else: # combi in args_dict
        print_this = str(combi) + " is already specified from a user provided args_file."
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      write_this = str(ORGXY) + " to write into XDS.INP: " + str(args_dict[combi])
      util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    else: # For smv input folder, args_dict['sections'] != 1 (could be 120)
      #args_dict["file_format_for_ORGXY"] = "smv_then_png"
      args_dict["file_format_for_ORGXY"] = "smv_itself"

      combi = (ORGXY, str(mrc_wo_path_wo_ext)) 
      
      if (combi not in args_dict):
        print_this = "(note)  AutoMicroED doesn't see " + str(ORGXY) + " in a user-provided args_file."
        print_this = print_this + "\n\t\t\t\tTherefore, it will estimate " + str(ORGXY) + " using matplotlib."
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])

        print_this = "\tsmv_folder:" + str(mrc_or_mrcs_w_path)
        #/home/kimd999/gpustorage/DN/microED/small/acet_fastest_and_unit_tests/user_provided_smv/output/keep_smv_test_20220314_15_55_45/archive/170629merged/img
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])

        glob_this = os.path.join(mrc_or_mrcs_w_path,"*.img")
        list_of_img = glob.glob(glob_this)  

        random_index = random.randint(3, int(len(list_of_img)/3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result1 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result1 == -999):
          exit(1)

        random_index = random.randint(int(len(list_of_img)/3), 2*int(len(list_of_img)/3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result2 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result2 == -999):
          exit(1)

        random_index = random.randint(2*int(len(list_of_img)/3), int(len(list_of_img)-3))
        use_this_input_smv_file = list_of_img[random_index]
        print_this = "\tA smv file that will be used to estimate " + str(ORGXY) + ": " + str(use_this_input_smv_file)
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
        result3 = estimate_ORGXY_for_smv_itself(args_dict, str(ORGXY), use_this_input_smv_file)
        if (result3 == -999):
          exit(1)

        args_dict[combi] = round(((result1 + result2 + result3)/3),2)

        print_this = "\t\t(Tip) Enter \"bypass\" and hit enter key if a user wants to add current " + str(ORGXY) \
                   + " in an argument file (so that this automatic estimation of " + str(ORGXY) + " can be bypassed next time when user runs AutoMicroED again).\n"
        print_this = print_this + "\t\t(Tip) Otherwise (a user doesn't want to add this estimated " + str(ORGXY) + " to argumenr file, just hit enter key only.\n"
        
        if ("kimd999" in home_dir_path):
            util.nonBlockingRawInput(print_this)
        else:
          bypass_can = input(print_this)
          if (bypass_can.rstrip() == "bypass") or (bypass_can.rstrip() == "\"bypass\""):
            f_out = codecs.open("../../../../args_file_generated_by_AutoMicroED.txt", 'a')
            
            write_this = str(ORGXY) + " " + str(str(input_smv_file_wo_ext_wo_path_w_4_question_marks)) + " " + str(args_dict[combi]) + " # generated by AutoMicroED\n"
            
            f_out.write(write_this)
            f_out.close()
      ##### end of if (combi not in args_dict):

      else: # combi in args_dict
        print_this = str(combi) + " is already specified from a user provided args_file."
        util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      write_this = str(ORGXY) + " to write into XDS.INP: " + str(args_dict[combi])
      util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  ##### <end> assign ORGX/ORGY in XDS.INP

  
  if ("ROTATION_AXIS" not in args_dict):
    args_dict['ROTATION_AXIS'] = "-1 0 0" # James wants to use -1 0 0
  write_this = "ROTATION_AXIS to use in XDS.INP: " + str(args_dict['ROTATION_AXIS'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])

  
  if ("spot2pdb_RESOLUTION_RANGE_max" in args_dict):
    spot2pdb_RESOLUTION_RANGE_max = args_dict['spot2pdb_RESOLUTION_RANGE_max']
  else:
    spot2pdb_RESOLUTION_RANGE_max = receive_from_user("spot2pdb_RESOLUTION_RANGE_max")
    args_dict['spot2pdb_RESOLUTION_RANGE_max'] = spot2pdb_RESOLUTION_RANGE_max
  write_this = "spot2pdb_RESOLUTION_RANGE_max from a user: " + str(spot2pdb_RESOLUTION_RANGE_max)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])


  if ("spot2pdb_RESOLUTION_RANGE_min" in args_dict):
    spot2pdb_RESOLUTION_RANGE_min = args_dict['spot2pdb_RESOLUTION_RANGE_min']
  else:
    spot2pdb_RESOLUTION_RANGE_min = receive_from_user("spot2pdb_RESOLUTION_RANGE_min")
    args_dict['spot2pdb_RESOLUTION_RANGE_min'] = spot2pdb_RESOLUTION_RANGE_min
  write_this = "spot2pdb_RESOLUTION_RANGE_min from a user: " + str(spot2pdb_RESOLUTION_RANGE_min)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])


  if ("TEST_RESOLUTION_RANGE_max" in args_dict):
    TEST_RESOLUTION_RANGE_max = args_dict['TEST_RESOLUTION_RANGE_max']
  else:
    TEST_RESOLUTION_RANGE_max = receive_from_user("TEST_RESOLUTION_RANGE_max")
    args_dict['TEST_RESOLUTION_RANGE_max'] = TEST_RESOLUTION_RANGE_max
  write_this = "TEST_RESOLUTION_RANGE_max from a user: " + str(TEST_RESOLUTION_RANGE_max)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  
  if ("TEST_RESOLUTION_RANGE_min" in args_dict):
    TEST_RESOLUTION_RANGE_min = args_dict['TEST_RESOLUTION_RANGE_min']
  else:
    TEST_RESOLUTION_RANGE_min = receive_from_user("TEST_RESOLUTION_RANGE_min")
    args_dict['TEST_RESOLUTION_RANGE_min'] = TEST_RESOLUTION_RANGE_min
  write_this = "TEST_RESOLUTION_RANGE_min from a user: " + str(TEST_RESOLUTION_RANGE_min)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  
  if ("TRUSTED_REGION_min" not in args_dict):
    args_dict['TRUSTED_REGION_min'] = "0.0"
  if ("TRUSTED_REGION_max" not in args_dict):
    args_dict['TRUSTED_REGION_max'] = "1.4142"

  write_this = "TRUSTED_REGION_min to use: " + str(args_dict['TRUSTED_REGION_min'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  write_this = "TRUSTED_REGION_max to use: " + str(args_dict['TRUSTED_REGION_max'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  templates_path = args_dict['repo_location'] + "/templates/"
  XDS_INP_w_path = os.path.join(templates_path, "XDS_template.INP")
  shutil.copyfile(XDS_INP_w_path, os.path.join(os.getcwd(),"XDS_template.INP"))
  ###### <end> just check args_dict to prepare XDS.INP to process each mrc
  

  #xds_kind_list = ["xds_par"]
  '''
  xds_kind_list = ["xds_par"]
  if ('multi_core_xds' in args_dict):
    if (
       (str(args_dict['multi_core_xds']).upper() == "FALSE")
       or (str(args_dict['multi_core_xds']).upper() == "F")
       ):
      xds_kind_list = ["xds"]
  '''

  
  #xds_kind_list = ["xds_par", "xds"]
  # try both because of racing condition error
  # however, xds_par got stuck 10/4/2021 maybe because that krios_gpu uses 20 cores for other jobs
  
  xds_kind_list = ["xds"]
  #When krios_gpu uses ~50 cores at once (6/22/2022), xds_par silently got stuck

  for xds_kind in xds_kind_list:
    process = str(xds_kind) + " to process " + str(mrc_or_mrcs_w_path)
    util.show_header(process)
    start_time = time.time()
    
    args_dict['extra_xds_option'] = ""
    
    returned_from_run_all_xds = \
    run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind)

    if (returned_from_run_all_xds == None):
      write_this = "Running xds returned None, please email doonam.kim@pnnl.gov"
      util.flog(write_this, args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
      return False

    if (returned_from_run_all_xds != True) and (returned_from_run_all_xds != False):
      xds_log_filename_wo_ext = returned_from_run_all_xds
    
      xds_log_filename_w_ext_that_generates_CORRECT_LP \
        = returned_from_run_all_xds + "_" + str(xds_kind) + ".log"
    
      shutil.copyfile(xds_log_filename_w_ext_that_generates_CORRECT_LP, "XDS_that_generates_CORRECT_LP.log")

    if (os.path.isfile("CORRECT.LP") == False):
      add_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
      args_dict['extra_xds_option'] = "BEAM_DIVERGENCE_REFLECTING_RANGE"
      shutil.move("XDS.INP", "XDS_template.INP")
      
      returned_from_run_all_xds = \
      run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind)
      if (returned_from_run_all_xds != True) and (returned_from_run_all_xds != False):
        xds_log_filename_wo_ext = returned_from_run_all_xds
        xds_log_filename_w_ext_that_generates_CORRECT_LP \
          = returned_from_run_all_xds + "_" + str(xds_kind) + ".log"
        shutil.copyfile(xds_log_filename_w_ext_that_generates_CORRECT_LP, "XDS_that_generates_CORRECT_LP.log")
      
      if (os.path.isfile("CORRECT.LP") == False):
        remove_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
  
    if (os.path.isfile("CORRECT.LP") == False):
      args_dict['extra_xds_option'] = "DELPHI_10"
      add_DELPHI_10(args_dict['logfile_name_w_abs_path'])
      shutil.move("XDS.INP", "XDS_template.INP")
      
      returned_from_run_all_xds = \
      run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind)
      if (returned_from_run_all_xds != True) and (returned_from_run_all_xds != False):
        xds_log_filename_wo_ext = returned_from_run_all_xds
        xds_log_filename_w_ext_that_generates_CORRECT_LP \
          = returned_from_run_all_xds + "_" + str(xds_kind) + ".log"
        shutil.copyfile(xds_log_filename_w_ext_that_generates_CORRECT_LP, "XDS_that_generates_CORRECT_LP.log")
      
      if (os.path.isfile("CORRECT.LP") == False):
        remove_DELPHI_10(args_dict)
    
    if (os.path.isfile("CORRECT.LP") == False):
      args_dict['extra_xds_option'] = "BEAM_DIVERGENCE_REFLECTING_RANGE_DELPHI_10"
      add_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
      add_DELPHI_10(args_dict['logfile_name_w_abs_path'])
      shutil.move("XDS.INP", "XDS_template.INP")
      
      returned_from_run_all_xds \
        = run_all_xds(args_dict, mrc_wo_path, output_folder_name, xds_kind)
      if (returned_from_run_all_xds != True) and (returned_from_run_all_xds != False):
        xds_log_filename_wo_ext = returned_from_run_all_xds
        xds_log_filename_w_ext_that_generates_CORRECT_LP \
          = returned_from_run_all_xds + "_" + str(xds_kind) + ".log"
        shutil.copyfile(xds_log_filename_that_generates_CORRECT_LP, "XDS_that_generates_CORRECT_LP.log")
      
      if (os.path.isfile("CORRECT.LP") == False):
        remove_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
        remove_DELPHI_10(args_dict)

    if (os.path.isfile("CORRECT.LP") == False):
      util.flog(message_for_CORRECT_LP_not_found, args_dict['logfile_name_w_abs_path'])
      return "CORRECT.LP not found"
    else:
      util.flog("[xds] CORRECT.LP found", args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print("[xds] CORRECT.LP found", args_dict['summary_logfile_name_w_abs_path'])
      loop_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict, xds_log_filename_wo_ext, xds_kind, \
        xds_log_filename_w_ext_that_generates_CORRECT_LP)

      # run xds one last time with final files (the latest xds.INP, XPARM.XDS and GXPARM.XDS) 
      # from the former xds run that yielded the highest ISa.

      xds_log_filename_wo_ext = "XDS_final"
      output_report_file_name = run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)

      ISa = get_ISa(args_dict, output_report_file_name)

      print_this = "The highest possible ISa for this dataset: " + str(ISa)

      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])


    the_highest_COMPLETENESS = 0 #initial value
    CORRECT_LP = codecs.open("CORRECT.LP", 'r')
    for line in CORRECT_LP:
      splited_line = line.split()
      if (len(splited_line) == 14):
        COMPLETENESS_percent = splited_line[4]
        if ("%" in COMPLETENESS_percent):
          splited_COMPLETENESS_percent = COMPLETENESS_percent.split("%")
          COMPLETENESS = float(splited_COMPLETENESS_percent[0])
          if (COMPLETENESS > the_highest_COMPLETENESS):
            the_highest_COMPLETENESS = COMPLETENESS
  
    write_this = "The highest COMPLETENESS (in CORRECT.LP) for this dataset:" + str(the_highest_COMPLETENESS) + "%\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    util.flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
    
    if ('least_completeness_overall' not in args_dict.keys()):
      args_dict['least_completeness_overall'] = receive_from_user("least_completeness_overall")
    if (float(the_highest_COMPLETENESS) > float(args_dict['least_completeness_overall'])):
      write_this = "Current_COMPLETENESS is > target_COMPLETENESS (e.g. " + str(args_dict['least_completeness_overall']) +"%). Therefore, no more crystal is needed for reconstruction."
      more_crystal_needed = False
    else:
      write_this = "Current_COMPLETENESS is <= target_COMPLETENESS (e.g. " + str(args_dict['least_completeness_overall']) +"%). Therefore, more crystal is needed for reconstruction."
      more_crystal_needed = True
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    end_time = time.time()
    
    write_this = util.show_time(process, start_time, end_time)
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    # (devel) even at thend of run_xds, XSCALE.LP is still not made
    return more_crystal_needed
######### end of def run_xds(logfile_name_w_abs_path, mrc_or_mrcs_w_path, repo_location, output_folder_name)

'''
def run_xds_at_PNNL_HPC_Cascade_w_sbatch(repo_location, command, output_report_file_name):
  
    #open_this_template_file = str(repo_location) + "/templates/slurm_template_GPU"
    # 07/30/2020, pncc is very busy, can't run
  
    open_this_template_file = str(repo_location) + "/templates/slurm_template_emsls50432"
    new_slurm_script_file_name = "slurm_xds"
    
    line_is_str = False
    f_in  = codecs.open(open_this_template_file, 'r')
    f_out = codecs.open(new_slurm_script_file_name, 'wb')
    for line in f_in:
      if (type(line) == str):
        line_is_str = True
        f_out.close()
        f_in.close()
        break
      else:
        f_out.write(line)
    if (line_is_str == False):
      f_out.write(command + "\n")
      f_out.close()
      f_in.close()
    
    if (line_is_str == True):
      f_in  = codecs.open(open_this_template_file, 'r')
      f_out = codecs.open(new_slurm_script_file_name, 'w')
      for line in f_in:
        f_out.write(line)
      f_out.write(command + "\n")
      f_out.close()
      f_in.close()

    while (True):
      number_of_pending_or_active_jobs = subprocess.check_output(command_for_number_of_pending_or_active_jobs, shell=True)
      if (int(number_of_pending_or_active_jobs) < 12):
          launch_cascade_jobs(new_slurm_script_file_name)
          break
      time.sleep(1)
          
    while (True):
      print ("\n\nAutoMicroED is running xds.")
      print_this = "\t(xds will keep running until it finds " + str(output_report_file_name) + " and confirms that its size doesn't change anymore.)"
      print (print_this)
      
      waiting(10)
      number_of_pending_or_active_jobs = subprocess.check_output(command_for_number_of_pending_or_active_jobs, shell=True)
      number_of_pending_jobs = subprocess.check_output(command_for_number_of_pending_jobs, shell=True)
      number_of_active_jobs = subprocess.check_output(command_for_number_of_active_jobs, shell=True)
      print ("\tnumber of pending or active jobs:" + str(number_of_pending_or_active_jobs.decode('utf-8')))
      print ("\tnumber of pending jobs:" + str(number_of_pending_jobs.decode('utf-8')))
      
      if (int(number_of_pending_or_active_jobs) == 0):
        print ("no pending or active jobs")
        break
      
      print ("\tnumber of active jobs:" + str(number_of_active_jobs.decode('utf-8')))
      if (int(number_of_active_jobs) == 0):
        print ("cascade job is not launched yet")
        print ("\t(Once launched, xds with ~70 images took ~3 minutes.)\n")
      
      if (os.path.isfile(output_report_file_name) == False):
        continue
      file_size_of_report_file = file_size(output_report_file_name)
      waiting(30)
      file_size_of_report_file2 = file_size(output_report_file_name)
      if (file_size_of_report_file == file_size_of_report_file2):
        break
######### end of def run_xds_at_PNNL_HPC_Cascade_w_sbatch(repo_location, output_report_file_name)
'''


def run_xds_now(args_dict, prefix_of_file_name, xds_kind):  
  INP_file_name = prefix_of_file_name + ".INP"
  shutil.copyfile("XDS.INP", INP_file_name)
  output_report_file_name = prefix_of_file_name + "_" + str(xds_kind) + ".log"
  
  # sometimes xds_par works, sometimes xds works -> really ?
  ''' !!! ERROR !!! CANNOT OPEN OR READ FILE bin1_01.tmp
               Presumably, the independent jobs supposed to have been started
               in the INTEGRATE step have not run properly. This could be due
               to incomplete installation of XDS where some of the executables
               of the package are not included in the search path.
               '''
  
  # xds_kind is either xds or xds_par
  #command = str(xds_kind) + " > " + str(output_report_file_name)

  #command = "/opt/apps/XDS-INTEL64_Linux_x86_64/xds > " + str(output_report_file_name)
  #command = "/opt/apps/XDS-INTEL64_Linux_x86_64/xds_par > " + str(output_report_file_name)

  #command = "xds_par > " + str(output_report_file_name)
  command = "xds > " + str(output_report_file_name)

  

  # xds always runs XDS.INP, even if I typed xds XDS_all.INP
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  
  xds_ran = False
  # if ("PNNL_HPC_Cascade_sbatch" in args_dict):
  #   if ((platform.system() == "Linux") and (args_dict['PNNL_HPC_Cascade_sbatch'] == "True")):
  #     run_xds_at_PNNL_HPC_Cascade_w_sbatch(args_dict['repo_location'], command, output_report_file_name)
  #     xds_ran = True
  if (xds_ran == False):
    
    util.flog("\t(note) In one linux machine, xds_par for 70 images took 2 minutes.)", args_dict['logfile_name_w_abs_path'])
    # this is based on PNNL_HPC_cascade

    os.system(command)
  return output_report_file_name
######### end of def run_xds_now(prefix_of_file_name)    


def XDS_default(args_dict, mrc_wo_path, output_folder_name, xds_kind):
  if (args_dict['input_list_has_mrc'] == False):
    mrc_wo_path = output_folder_name

  mrc_wo_path_wo_ext = os.path.splitext(mrc_wo_path)[0]

  if (args_dict['input_list_has_mrc'] == False):
    mrc_wo_path_wo_ext_w_4_question_marks = mrc_wo_path_wo_ext + "_????"
  else:
    mrc_wo_path_wo_ext_w_4_question_marks = mrc_wo_path_wo_ext[:-5] + "_????"
  
  f_in  = codecs.open("XDS_template.INP", 'r') 
  
  new_XDS_INP_file_name = "XDS.INP"
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  
  for line in f_in:
    if (line[:17] == "BACKGROUND_RANGE="):
      write_this = "BACKGROUND_RANGE=" + str(args_dict['min_DATA_RANGE']) + " " + str(args_dict['max_DATA_RANGE']) + "\n"
      f_out.write(write_this)
    elif (line[:15] == "CLUSTER_RADIUS="):
      write_this = "CLUSTER_RADIUS=7 \n"
      f_out.write(write_this)
    elif (line[:11] == "DATA_RANGE="):
      write_this = "DATA_RANGE=" + str(args_dict['min_DATA_RANGE']) + " " \
        + str(args_dict['max_DATA_RANGE']) + "\n"
      f_out.write(write_this)
    elif (line[:18] == "DETECTOR_DISTANCE="):
      if 'd_calibrated' not in args_dict:
        #print (f"args_dict['sections']:{args_dict['sections']}")
        # tutorial -> 120
        # smv only -> 120
        
        #print (f"mrc_wo_path_wo_ext:{mrc_wo_path_wo_ext}")
        # smv only -> 170629merged

        if (int(args_dict['sections']) != 1):
          combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext))
        else:
          combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext_w_4_question_marks))
        
        #print (f"combi_d_calibrated:{combi_d_calibrated}")
        # tutorial -> ('d_calibrated', '165749merged')
        # smv only -> ('d_calibrated', '170629merged')

        #print (f"args_dict:{args_dict}")
        write_this = "DETECTOR_DISTANCE=" + str(args_dict[combi_d_calibrated]) + "\n"
      else:
        write_this = "DETECTOR_DISTANCE=" + str(args_dict['d_calibrated']) + "\n"
      f_out.write(write_this)
    elif (line[:27] == "! INCLUDE_RESOLUTION_RANGE="):
      write_this = "INCLUDE_RESOLUTION_RANGE=" + str(args_dict['INCLUDE_RESOLUTION_RANGE']) + " \n"
      f_out.write(write_this)
    elif (line[:29] == "NAME_TEMPLATE_OF_DATA_FRAMES="):
      os.chdir("..")
      cwd = os.getcwd() # this is essential, weird, but keep this

      img_folder = os.path.join(os.path.normpath(cwd), "img")
      if 'prefix_of_img_file' in args_dict:
        # newer (more generalizable) method
        prefix_folder = os.path.join(img_folder, args_dict['prefix_of_img_file'])
      else:
        # old method
        prefix_folder = os.path.join(img_folder, output_folder_name)

      os.chdir("xds")
      path_of_img = prefix_folder + "_????.img"

      ## <begin> check whether user specifies imge name as output_folder_name or prefix_of_img_file
      prefix_of_img_file_exists = False
      output_folder_name_exists = False
      for each_img_file in os.listdir(img_folder):
        if each_img_file.endswith(".img"): # this is smv file
          if 'prefix_of_img_file' in args_dict:
            if args_dict['prefix_of_img_file'] in each_img_file:
              prefix_of_img_file_exists = True
          if output_folder_name in each_img_file:
            output_folder_name_exists = True
          if (output_folder_name_exists == False) and (prefix_of_img_file_exists == True):
            args_dict['user_named_img_file_wo_output_folder_name'] = True
            # e.g. just 112002_0001.img
          else:
            args_dict['user_named_img_file_wo_output_folder_name'] = False
            # e.g. 20181220-112002_0001.img
          break
      ## <end> check whether user specifies imge name as output_folder_name or prefix_of_img_file

      write_this = "NAME_TEMPLATE_OF_DATA_FRAMES=" + str(path_of_img) + "\n"
      f_out.write(write_this)
    elif (line[:3] == "NX="):
      if ('NX' in args_dict.keys()):
          write_this = "NX=" + str(args_dict['NX']) + " \n"
      else:
        args_dict['NX'] = receive_from_user("NX")
        write_this = "NX=" + str(args_dict['NX']) + " \n"
      f_out.write(write_this)
      '''# Number of "fast" pixels in a data image along X.
         # Used by XYCORR, INIT, COLSPOT, IDXREF.
         # IMOD's command, header <mrc/mrcs filename> will show number of columns, rows.
         # Therefore, AutoMicroED just uses this value as NX.'''
    elif (line[:3] == "NY="):
      if ('NY' in args_dict.keys()):
          write_this = "NY=" + str(args_dict['NY']) + " \n"
      else:
        args_dict['NY'] = receive_from_user("NY")
        write_this = "NY=" + str(args_dict['NY']) + " \n"
      f_out.write(write_this)
    elif (line[:7] == "OFFSET="):
      write_this = "OFFSET=128\n"
      f_out.write(write_this)
    elif (line[:5] == "ORGX="):
      if ("ORGX" in args_dict):
        write_this = "ORGX=" + str(args_dict["ORGX"]) + "\n"
        f_out.write(write_this)
      else:
        if (args_dict['input_list_has_mrc'] == False):
          for i in range(len(list(args_dict.keys()))):
            if (len(list(args_dict.keys())[i])) == 2:
              if str(list(args_dict.keys())[i][0]) == "ORGX":
                ORGX = list(args_dict.values())[i]
          write_this = "ORGX=" + str(ORGX) + "\n"
          f_out.write(write_this)
        else:
          if (int(args_dict['sections']) > 1):
            combi = ('ORGX', str(mrc_wo_path_wo_ext))
          else:
            combi = ('ORGX', str(mrc_wo_path_wo_ext_w_4_question_marks))

          if (combi in args_dict):
            write_this = "ORGX=" + str(args_dict[combi]) + "\n"
            f_out.write(write_this)
          else:
            f_out.write(line)
      
    elif (line[:5] == "ORGY="):
      if ("ORGY" in args_dict):
        write_this = "ORGY=" + str(args_dict["ORGY"]) + "\n"
        f_out.write(write_this)
      else:
        if (args_dict['input_list_has_mrc'] == False):
          for i in range(len(list(args_dict.keys()))):
            if (len(list(args_dict.keys())[i])) == 2:
              if str(list(args_dict.keys())[i][0]) == "ORGY":
                ORGY = list(args_dict.values())[i]
          write_this = "ORGY=" + str(ORGY) + "\n"
          f_out.write(write_this)
        else:
          if (int(args_dict['sections']) > 1):
            combi = ('ORGY', str(mrc_wo_path_wo_ext))
          else:
            combi = ('ORGY', str(mrc_wo_path_wo_ext_w_4_question_marks))

          if (combi in args_dict):
            write_this = "ORGY=" + str(args_dict[combi]) + "\n"
            f_out.write(write_this)
          else:
            f_out.write(line)

    elif (line[:18] == "OSCILLATION_RANGE="):
      if (args_dict['input_list_has_mrc'] == True):
        if (int(args_dict['sections']) != 1):
          if "E" not in args_dict:
            if "r" not in args_dict:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext)])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext)])) + " \n"
            else:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext)])) + " \n"
          else:
            if "r" not in args_dict:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext)])\
                                                     *float(args_dict['E'])) + " \n"
            else:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E'])) + " \n"
        else:
          if "E" not in args_dict:
            if "r" not in args_dict:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext_w_4_question_marks)])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext_w_4_question_marks)])) + " \n"
            else:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext_w_4_question_marks)])) + " \n"
          else:
            if "r" not in args_dict:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext_w_4_question_marks)])\
                                                     *float(args_dict['E'])) + " \n"
            else:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E'])) + " \n"
      
      else:
        if "E" not in args_dict:
          if "r" not in args_dict:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext)])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext)])) + " \n"
          else:
              write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E', str(mrc_wo_path_wo_ext)])) + " \n"
        else:
          if "r" not in args_dict:
            write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r', str(mrc_wo_path_wo_ext)])\
                                                   *float(args_dict['E'])) + " \n"
          else:
            write_this = "OSCILLATION_RANGE=" + str(float(args_dict['r'])\
                                                     *float(args_dict['E'])) + " \n"
            
      f_out.write(write_this)
      '''# Oscillation range of each data image in degree.
         # This will be automatically calculated as r x E
         # For ketone data, 0.899999976 worked
         # I know that positive multiple of 0.0001 is "required", but for ketone data, it was not required.
         # If there are 130 images for -65 and 65, using 1 makes sense
         # It must be a positive multiple of 0.0001. Thus, a value like 0.000125 would be incorrect! XDS assumes a right handed rotation of the crystal about the rotation axis when proceeding to the next data image. No sensible default value can be provided and the user must insert the correct value. For detectors with no read-out noise like the PILATUS an optimal choice for the oscillation range would match half of the crystal's mosaicity (defined as the standard deviation of the reflecting range). A further reduction of the oscillation range could lead to problems in the accurate determination of extremely low background and unreliably processed data.
         # This describes a "fine-sliced" data set with each image covering an oscillation range of 0.1 °.
         # Parameter is used by IDXREF'''
    
    elif (line[:3] == "QX="):
      write_this = "QX=" + str(args_dict['P']) + " \n"
      f_out.write(write_this)
    elif (line[:3] == "QY="):
      write_this = "QY=" + str(args_dict['P']) + " \n"
      f_out.write(write_this)
      '''!QX                                    # Pixels along X (mm)
         !QY                                    # Pixels along Y (mm)
         # These two will be automatically assigned from P'''
    

    elif (line[:14] == "ROTATION_AXIS="):
      write_this = "ROTATION_AXIS=" + str(args_dict['ROTATION_AXIS']) + " \n"
      f_out.write(write_this)
    

    elif (line[:7] == "SEPMIN="):
      write_this = "SEPMIN=14\n"
      f_out.write(write_this)
    

    elif (line[:19] == "SPACE_GROUP_NUMBER="):
      if ('SPACE_GROUP_NUMBER' in args_dict):
        write_this = "SPACE_GROUP_NUMBER=" + str(args_dict['SPACE_GROUP_NUMBER']) + "\n"
        f_out.write(write_this) # here f_out is "XDS.INP"
      else:
        write_this = "SPACE_GROUP_NUMBER=0\n"
        f_out.write(write_this)
    

    elif (line[:15] == "STARTING_ANGLE="):
      if (args_dict['input_list_has_mrc'] == True):
        if (int(args_dict['sections']) != 1):
          combi = ('STARTING_ANGLE', str(mrc_wo_path_wo_ext))
        else:
          combi = ('STARTING_ANGLE', str(mrc_wo_path_wo_ext_w_4_question_marks))
      else:
        if (args_dict['user_named_img_file_wo_output_folder_name'] == True):
          mrc_wo_path_wo_ext = args_dict['prefix_of_img_file'] + "_????"

        combi = ('STARTING_ANGLE', str(mrc_wo_path_wo_ext))
      
      if (combi in args_dict.keys()):
        write_this = "STARTING_ANGLE=" + str(args_dict[combi]) + "\n"
        # just put \n for writing into XDS.INP
        f_out.write(write_this)
      else:
        f_out.write(line)
      util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    

    elif (line[:22] == "TEST_RESOLUTION_RANGE="):
      write_this = "TEST_RESOLUTION_RANGE=" + str(args_dict['TEST_RESOLUTION_RANGE_max']) + " " \
         + str(args_dict['TEST_RESOLUTION_RANGE_min']) + "\n"
      f_out.write(write_this)
    

    elif (line[:15] == "TRUSTED_REGION="):
      write_this = "TRUSTED_REGION=" + str(args_dict['TRUSTED_REGION_min']) + " " + \
        str(args_dict['TRUSTED_REGION_max']) + "\n"
      f_out.write(write_this)
    

    elif (line[:20] == "UNIT_CELL_CONSTANTS="):
      if ('UNIT_CELL_CONSTANTS' in args_dict):
        write_this = "UNIT_CELL_CONSTANTS=" + str(args_dict['UNIT_CELL_CONSTANTS']) 
        f_out.write(write_this)
      else:
        write_this = "UNIT_CELL_CONSTANTS=70 80 90 90 90 90\n"
        f_out.write(write_this)

        #write_this = "\t(note) For ketone data set, UNIT_CELL_CONSTANTS does not need to be specified."
        #util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    

    elif (line[:17] == "X-RAY_WAVELENGTH="):
      if ((args_dict['voltage_of_the_microscope'] == "300") or (int(args_dict['voltage_of_the_microscope']) == 300)):
        write_this = "X-RAY_WAVELENGTH=0.0196\n"
      else:
        write_this = "X-RAY_WAVELENGTH=0.0251\n"
      '''! Wavelength of the incident X-ray beam (angstrom). 
         ! old explanation -> For example, it could be 0.92 when a synchrotron data set collected at wavelength 0.92 angstrom. Used by IDXREF
         ! Since there is no X-RAY in microED, this is actually wavelength of electron'''
      f_out.write(write_this)
    
    else:
      f_out.write(line)
  
  if (args_dict['extra_xds_option'] == ""):
    combi = ('EXCLUDE_DATA_RANGE', str(mrc_wo_path_wo_ext)) #mrc_wo_path has .mrc extension

    if (combi in args_dict.keys()):
      write_this = str(args_dict[combi]) + "\n"
      f_out.write(write_this)

    combi = ('EXCLUDE_DATA_RANGE', str(mrc_wo_path_wo_ext_w_4_question_marks))

    if (combi in args_dict.keys()):
      write_this = str(args_dict[combi]) + "\n"
      f_out.write(write_this)
    
    # print_this = "\nPress enter to continue.\n"
    # input(print_this)
  
  f_in.close()
  f_out.close()
  
  util.flog("\t(note) INTEGRATE is the most important step (\"JOB\") of XDS.", args_dict['logfile_name_w_abs_path'])
  util.flog("\t       It determines the intensity of each reflection predicted to occur in the rotation data images (DATA_RANGE=) and saves the results on file INTEGRATE.HKL.", \
       args_dict['logfile_name_w_abs_path'])
  util.flog("\t       It writes the logfile \"INTEGRATE.LP\".\n", args_dict['logfile_name_w_abs_path'])
  
  xds_log_filename_wo_ext = "XDS_default"
  if (args_dict['extra_xds_option'] != ""):
    xds_log_filename_wo_ext = xds_log_filename_wo_ext + "_" + str(args_dict['extra_xds_option'])
  output_report_file_name = run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)
  return xds_log_filename_wo_ext
######### end of def XDS_default(logfile_name_w_abs_path, repo_location, output_folder_name):


def XDS_half_SPOT_RANGE_and_full_BACKGROUND_RANGE(args_dict, output_folder_name, xds_kind):
  shutil.move("XDS.INP", "XDS_template.INP")
  f_in  = codecs.open("XDS_template.INP", 'r')
  new_XDS_INP_file_name = "XDS.INP"
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    if (line[:17] == "BACKGROUND_RANGE="):
      write_this = "BACKGROUND_RANGE=" + str(args_dict['min_DATA_RANGE']) + " " + str(args_dict['max_DATA_RANGE']) + "\n"
      f_out.write(write_this)
    elif (line[:11] == "SPOT_RANGE="):
      min_SPOT_RANGE = max(3, (int(args_dict['min_DATA_RANGE'])//2))
      write_this = "SPOT_RANGE=" + str(args_dict['min_DATA_RANGE']) + " " + str(int(args_dict['max_DATA_RANGE'])//2) + " \n"
      f_out.write(write_this)
    else:
      f_out.write(line)
  f_in.close()
  f_out.close()
  os.remove("XDS_template.INP")
  
  xds_log_filename_wo_ext = "XDS_half_SPOT_RANGE_and_full_BACKGROUND_RANGE"
  if (args_dict['extra_xds_option'] != ""):
    xds_log_filename_wo_ext = xds_log_filename_wo_ext + "_" + str(args_dict['extra_xds_option'])
  run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)
  return xds_log_filename_wo_ext
############# end of def XDS_half_SPOT_RANGE_and_full_BACKGROUND_RANGE()


def XDS_shorter_JOB(args_dict, xds_kind):
  util.flog("CORRECT.LP not found.", args_dict['logfile_name_w_abs_path'])
  util.flog("Therefore, AutoMicroED will try JOB=DEFPIX INTEGRATE CORRECT only\n", \
    args_dict['logfile_name_w_abs_path'])
  shutil.move("XDS.INP", "XDS_template.INP")
  f_in  = codecs.open("XDS_template.INP", 'r')
  new_XDS_INP_file_name = "XDS.INP"
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    if (line[:4] == "JOB="):
      write_this = "JOB=DEFPIX INTEGRATE CORRECT\n"
      f_out.write(write_this)
    else:
      f_out.write(line)
  f_in.close()
  f_out.close()

  xds_log_filename_wo_ext = "XDS_shorter_JOB"
  if (args_dict['extra_xds_option'] != ""):
    xds_log_filename_wo_ext = xds_log_filename_wo_ext + "_" + str(args_dict['extra_xds_option'])
  run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)
  return xds_log_filename_wo_ext
############# end of def XDS_shorter_JOB()


def XDS_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict, xds_kind):
  util.flog("AutoMicroED will feed BEAM_DIVERGENCE and REFLECTING_RANGE with a hope for further improvement of I/sigma (ISa).\n", args_dict['logfile_name_w_abs_path'])
  BEAM_DIVERGENCE, REFLECTING_RANGE = get_BEAM_DIVERGENCE_REFLECTING_RANGE(args_dict)
  if (BEAM_DIVERGENCE == None):
    write_this = "BEAM_DIVERGENCE=None, exit now\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    return False
  
  shutil.move("XDS.INP", "XDS_template.INP")
  
  f_in  = codecs.open("XDS_template.INP", 'r')
  new_XDS_INP_file_name = "XDS.INP"
  f_out = codecs.open(new_XDS_INP_file_name, 'w')
  for line in f_in:
    f_out.write(line)
  f_in.close()
  
  write_this = "\nBEAM_DIVERGENCE=" + str(BEAM_DIVERGENCE) + "\n"
  f_out.write(write_this)
  # (Irina) the experiment was conducted 3 times, so the average value is 3 plus/minus 0.1. So 3 is an actual average value and 0.1 is ESD. The xds is only using 3.
  
  write_this = "REFLECTING_RANGE=" + str(REFLECTING_RANGE) + "\n"
  f_out.write(write_this)
  
  f_out.close()

  xds_log_filename = "XDS_BEAM_DIVERGENCE_REFLECTING_RANGE"
  if (args_dict['extra_xds_option'] != ""):
    xds_log_filename = xds_log_filename + "_" + str(args_dict['extra_xds_option'])
  run_xds_now(args_dict, xds_log_filename, xds_kind)
  return xds_log_filename
############# end of def XDS_BEAM_DIVERGENCE_REFLECTING_RANGE()


def XDS_sliding_SPOT_RANGE(args_dict, output_folder_name, xds_kind):
  
  starting_values_of_min_SPOT_RANGE = [3,40,80,120,160,200,240]
  
  for i in range(len(starting_values_of_min_SPOT_RANGE)):
    min_SPOT_RANGE = max(starting_values_of_min_SPOT_RANGE[i], (int(args_dict['min_DATA_RANGE'])))
    max_SPOT_RANGE = min((min_SPOT_RANGE+100), (int(args_dict['max_DATA_RANGE'])))
    
    shutil.move("XDS.INP", "XDS_template.INP")
    f_in  = codecs.open("XDS_template.INP", 'r')
    new_XDS_INP_file_name = "XDS.INP"
    f_out = codecs.open(new_XDS_INP_file_name, 'w')
    for line in f_in:
      if (line[:11] == "SPOT_RANGE="):
        write_this = "SPOT_RANGE=" + str(min_SPOT_RANGE) + " " + str(max_SPOT_RANGE) + " \n"
        f_out.write(write_this)
      else:
        f_out.write(line)
    f_in.close()
    f_out.close()
    
    xds_log_filename = "XDS_SPOT_RANGE_" + str(min_SPOT_RANGE) + "_" + str(max_SPOT_RANGE)
    if (args_dict['extra_xds_option'] != ""):
      xds_log_filename = xds_log_filename + "_" + str(args_dict['extra_xds_option'])
    run_xds_now(args_dict, xds_log_filename, xds_kind)
    
    return xds_log_filename
############# end of def XDS_sliding_SPOT_RANGE()


def XDS_shorter_DATA_RANGE_shorter_JOB(args_dict, xds_kind):
  util.flog("CORRECT.LP not found.", args_dict['logfile_name_w_abs_path'])
  util.flog("Therefore, AutoMicroED will try shorter DATA_RANGE and JOB=DEFPIX INTEGRATE CORRECT\n", args_dict['logfile_name_w_abs_path'])
  shutil.move("XDS.INP", "XDS_template.INP")
  f_in  = codecs.open("XDS_template.INP", 'r')
  f_out = codecs.open("XDS.INP", 'w')
  for line in f_in:
    if (line[:4] == "JOB="):
      write_this = "JOB=DEFPIX INTEGRATE CORRECT\n"
      f_out.write(write_this)
    elif (line[:11] == "DATA_RANGE="):
      write_this = "DATA_RANGE=" + str(int(args_dict['min_DATA_RANGE'])+2) + " " + str(int(args_dict['max_DATA_RANGE'])-2) + "\n"
      f_out.write(write_this)
    elif (line[:11] == "SPOT_RANGE="):
      write_this = "SPOT_RANGE=" + str(args_dict['min_DATA_RANGE']+2) + " " + str(args_dict['max_DATA_RANGE']-2) + "\n"
      f_out.write(write_this)
    elif (line[:17] == "BACKGROUND_RANGE="):
      write_this = "BACKGROUND_RANGE=" + str(args_dict['min_DATA_RANGE']+2) + " " + str(args_dict['max_DATA_RANGE']-2) + "\n"
      f_out.write(write_this)
    else:
      f_out.write(line)
  f_in.close()
  f_out.close()
  
  xds_log_filename_wo_ext = "XDS_shorter_DATA_RANGE_shorter_JOB"
  if (args_dict['extra_xds_option'] != ""):
    xds_log_filename_wo_ext = xds_log_filename_wo_ext + "_" + str(args_dict['extra_xds_option'])
  run_xds_now(args_dict, xds_log_filename_wo_ext, xds_kind)
  return xds_log_filename_wo_ext
############# end of def XDS_shorter_DATA_RANGE_shorter_JOB()
