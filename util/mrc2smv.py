from math import isclose
import argparse, codecs, glob, os, platform, random, shutil, signal, subprocess, sys, time
#import tifffile # needed for wcen only
from PIL import Image
import protein, shelx, xds, xscale
import util

home_dir_path = os.path.expanduser("~")
user_ID = os.path.basename(home_dir_path)

command_for_number_of_pending_or_active_jobs = "squeue | grep " + str(user_ID) + " | wc -l"
command_for_number_of_pending_jobs = "squeue | grep " + str(user_ID) + " | grep \" PD \" | wc -l"
command_for_number_of_active_jobs = "squeue | grep " + str(user_ID) + " | grep \" R \" | wc -l"

 
def prepare_d_calibrated(args_dict, output_folder_name):  
  print (f"prepare_d_calibrated fn")

  print (f"output_folder_name:{output_folder_name}")
  #165749merged

  process = "prepare d_calibrated with " + str(output_folder_name)
  util.show_header(process)
  start_time = time.time()
  
  mrc_wo_path_wo_ext = output_folder_name

  mrc_wo_path_wo_ext_w_4_questions_marks = mrc_wo_path_wo_ext + "_????"

  #print (f"mrc_wo_path_wo_ext:{mrc_wo_path_wo_ext}")
  # tutorial -> 165749merged

  #print (f"mrc_wo_path_wo_ext_w_4_questions_marks:{mrc_wo_path_wo_ext_w_4_questions_marks}")
  # tutorial -> 165749m__????

  ############### <begin> distance
  print ("\n-d: sample-detector distance (mm).")
  
  if (args_dict['input_list_has_mrc'] == False): #e.g. smv
    combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext))
  else:
    if (int(args_dict['sections']) > 1):
      combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext))
    else:
      combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext_w_4_questions_marks))
  
  '''
  if combi_d_calibrated not in args_dict:
    if (int(args_dict['sections']) != 1):
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext))
    else:
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext_w_4_questions_marks))
    if combi_d_not_calibrated not in args_dict:
      args_dict[combi_d_not_calibrated] = receive_from_user("-d_not_calibrated")
    write_this = "d_not_calibrated from user: " + str(args_dict[combi_d_not_calibrated]) + \
                " as the one displayed in user's cryo-EM machine (example, Krios)"
    util.flog(write_this, logfile_name_w_abs_path)
    '''
  
  if 'd_calibrated' not in args_dict:
    if (int(args_dict['sections']) > 1):
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext))
    else:
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext_w_4_questions_marks))
    if combi_d_not_calibrated not in args_dict:
      args_dict[combi_d_not_calibrated] = receive_from_user("-d_not_calibrated")
    write_this = "d_not_calibrated from user: " + str(args_dict[combi_d_not_calibrated]) + \
                " as the one displayed in user's cryo-EM machine (example, Krios)"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    
    if "d_calibration_1st_coef" not in args_dict:
      args_dict['d_calibration_1st_coef'] = receive_from_user("d_calibration_1st_coef")
    if "d_calibration_2nd_coef" not in args_dict:
      args_dict['d_calibration_2nd_coef'] = receive_from_user("d_calibration_2nd_coef")
    
    write_this = "This user entered distance (d_not_calibrated) will be calibrated.\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    write_this = "d_calibrated = d_not_calibrated x d_calibration_1st_coef + d_calibration_2nd_coef\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    args_dict[combi_d_calibrated] = float(args_dict[combi_d_not_calibrated]) \
                                  * float(args_dict['d_calibration_1st_coef'])\
                                 + (float(args_dict['d_calibration_2nd_coef']))
    
    write_this = str(args_dict[combi_d_calibrated]) + " = " + str(args_dict[combi_d_not_calibrated]) \
                 + " x " + str(args_dict['d_calibration_1st_coef']) \
                 + " + " + str(args_dict['d_calibration_2nd_coef'])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
    write_this = "d_calibrated that will be used for mrc2smv: " + str(args_dict[combi_d_calibrated])
    
  else:
    write_this = "d_calibrated that will be used for mrc2smv: " + str(args_dict['d_calibrated'])
    
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  ############### <end> distance
######### end of def prepare_d_calibrated(args_dict, output_folder_name)


def remove_first_and_last_image_files(output_folder_name):
  print_this = '''\t"IF THE CRYSTAL HAS SLIPPED AT THE BEGINNING OF DATA COLLECTION,
        YOU MAY CHOOSE TO SKIP SOME OF THE FIRST FRAMES BY CHANGING. THE "DATA_RANGE=" IN FILE "XDS.INP"
        AND START ALL OVER AGAIN"'''
  print (print_this)
  
  min_DATA_RANGE = 9999
  max_DATA_RANGE = -9999
  number_of_img_file = 0
  
  for img_file in glob.glob("*.img"):
    number_of_img_file = number_of_img_file + 1
    index = img_file[(len(img_file)-8):(len(img_file)-4)]
    if (int(index) < int(min_DATA_RANGE)):
      min_DATA_RANGE = index
    if (int(index) > int(max_DATA_RANGE)):
      max_DATA_RANGE = index
      
  print ("\nnumber_of_img_file:" + str(number_of_img_file))
  if (number_of_img_file == 0):
    print_this = "no img file found."
    print (print_this)
    exit(1)
    
  if (number_of_img_file < 3):
    return int(min_DATA_RANGE), int(max_DATA_RANGE)
  
  min_DATA_RANGE = int(min_DATA_RANGE) + 1
  max_DATA_RANGE = int(max_DATA_RANGE) - 1
  
  return int(min_DATA_RANGE), int(max_DATA_RANGE)
########## end of def remove_first_and_last_image_files()


def run_mrc2smv_by_PIL(args_dict, mrc_w_path, output_folder_name):
  process = "mrc2smv by PIL with " + str(mrc_w_path)
  util.show_header(process)
  start_time = time.time()
  
  im = Image.open(mrc_w_path)
  print(im.format, im.size, im.mode)
  im.show()
##### end of def run_mrc2smv_by_PIL(args_dict, mrc_w_path, output_folder_name):


def run_mrc2smv_by_tvips(args_dict, mrc_w_path, output_folder_name):  
  process = "mrc2smv by tvips with " + str(mrc_w_path)
  util.show_header(process)
  start_time = time.time()
  
  mrc_wo_path = os.path.basename(mrc_w_path)
  mrc_wo_path_wo_ext = os.path.splitext(mrc_wo_path)[0]
  mrc_wo_path_wo_ext_w_4_questions_marks = mrc_wo_path_wo_ext[:-5] + "_????"
  
  print ("AutoMicroED is generating mrc2smv command.")
  ############### <begin> check mrc2smv_folder
  if ('mrc2smv_folder' in args_dict.keys()):
    print_this = "mrc2smv_folder:" + str(args_dict['mrc2smv_folder'])
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = str(os.path.join(str(args_dict['mrc2smv_folder']), str("mrc2smv"))) + " -M 128 -v"
  else:
    try:
      path = subprocess.check_output(["which", "mrc2smv"]).decode('UTF-8')
      print_this = "path of mrc2smv:" + str(path)
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      command_for_mrc2smv = "mrc2smv -M 128 -v"
    except:
      print_this ="AutoMicroED can't find mrc2smv in args_file and user's PATH."
      print_this = print_this + "\nDownload tvips-tools-jiffies from https://cryoem.ucla.edu/downloads/snapshots"
      print_this = print_this + "\nThen add mrc2smv_folder to args_file and run AutoMicroED again."
      print_this = print_this + "\n\tsee (git repo)/templates/args_file/explanation_of_args.txt for more detail"
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      exit(1)
  ############### <end> check mrc2smv_folder
  

  print (f"mrc_wo_path_wo_ext:{mrc_wo_path_wo_ext}")
  # tutorial -> 165749merged
  # each mrc file -> 2021-06-15-165749_0004

  print (f"mrc_wo_path_wo_ext_w_4_questions_marks:{mrc_wo_path_wo_ext_w_4_questions_marks}")
  # tutorial -> 165749merged_????
  # each mrc file -> 2021-06-15-165749_0004_????


  ############### <begin> distance
  print ("\n-d: sample-detector distance (mm).")
  
  if (int(args_dict['sections']) > 1):
    combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext))
  else:
    combi_d_calibrated = ('d_calibrated', str(mrc_wo_path_wo_ext_w_4_questions_marks))
  
  
  if 'd_calibrated' not in args_dict:
    if (int(args_dict['sections']) > 1):
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext))
    else:
      combi_d_not_calibrated = ('d_not_calibrated', str(mrc_wo_path_wo_ext_w_4_questions_marks))
    if combi_d_not_calibrated not in args_dict:
      
      #args_dict[combi_d_not_calibrated] = receive_from_user("-d_not_calibrated")
      # error 3/15/2022

      args_dict[combi_d_not_calibrated] = util.receive_from_user("-d_not_calibrated")

    write_this = "d_not_calibrated from user: " + str(args_dict[combi_d_not_calibrated]) + \
                " as the one displayed in user's cryo-EM machine (example, Krios)"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    
    if "d_calibration_1st_coef" not in args_dict:
      args_dict['d_calibration_1st_coef'] = receive_from_user("d_calibration_1st_coef")
    if "d_calibration_2nd_coef" not in args_dict:
      args_dict['d_calibration_2nd_coef'] = receive_from_user("d_calibration_2nd_coef")
    
    write_this = "This user entered distance (d_not_calibrated) will be calibrated.\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    write_this = "d_calibrated = d_not_calibrated x d_calibration_1st_coef + d_calibration_2nd_coef\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    
    args_dict[combi_d_calibrated] = float(args_dict[combi_d_not_calibrated]) \
                                  * float(args_dict['d_calibration_1st_coef'])\
                                 + (float(args_dict['d_calibration_2nd_coef']))
    
    write_this = str(args_dict[combi_d_calibrated]) + " = " + str(args_dict[combi_d_not_calibrated]) \
                 + " x " + str(args_dict['d_calibration_1st_coef']) \
                 + " + " + str(args_dict['d_calibration_2nd_coef'])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
    write_this = "d_calibrated that will be used for mrc2smv: " + str(args_dict[combi_d_calibrated])
    command_for_mrc2smv = command_for_mrc2smv + " -d " + str(args_dict[combi_d_calibrated])
  else:
    write_this = "d_calibrated that will be used for mrc2smv: " + str(args_dict['d_calibrated'])
    command_for_mrc2smv = command_for_mrc2smv + " -d " + str(args_dict['d_calibrated'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  ############### <end> distance
  
  
  ############### <begin> binning factor
  print_this = "\n\n-B: binning factor. Binning is assumed to be equal in the horizontal and vertical directions."
  print_this = print_this + "\tketone tutorial -> 1"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  if "B" not in args_dict:
    args_dict['B'] = receive_from_user("-B")
  write_this = "B from user: " + str(args_dict['B'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  command_for_mrc2smv = command_for_mrc2smv + " -B " + str(args_dict['B'])
  ############### <end> binning factor

  
  ############### <begin> Voltage
  print ("\n\nVoltage of the microscope")
  print ("\tArctica/ketone tutorial -> 200")
  print ("\tKrios/EMPIAR-10293      -> 300")
  
  if "voltage_of_the_microscope" not in args_dict:
    args_dict['voltage_of_the_microscope'] = receive_from_user("voltage_of_the_microscope")
  
  if (args_dict['voltage_of_the_microscope'] == "200"):
    print_this = "A user entered 200 kV (Arctica). Therefore, AutoMicroED will assign -w 0.0251 as the wavelength of electron."
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -w 0.0251 "
  elif (args_dict['voltage_of_the_microscope'] == "300"):
    print_this = "A user entered 300 kV (Krios/ARM). Therefore, AutoMicroED will assign -w 0.0196 as the wavelength of electron (empiar-10293 assigns 0.0197)"
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -w 0.0196 "
  else:
    print_this = "Please enter either 200 or 300 only. Exit now."
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    exit(1)
  ############### <end> Voltage
  
  
  ############### <begin> rotation rate
  print ("\n\n-r: rotation rate of the stage (degree/second).")
  print ("\tEMPIAR-10293 -> 1")
  print ("\tketone tutorial -> 0.9")

  if "r" not in args_dict:
    if (int(args_dict['sections']) > 1):
      combi = ('r', str(mrc_wo_path_wo_ext)) # assumes that input mrc/mrc is stack
    else: # if (int(args_dict['sections']) == 1):
      combi = ('r', str(mrc_wo_path_wo_ext_w_4_questions_marks)) # assumes that input mrc/mrc is single 2D images
    
    if (combi not in args_dict):
      args_dict[combi] = receive_from_user("r")
      
    write_this = "r from user: " + str(args_dict[combi])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -r " + str(args_dict[combi])
  else:
    write_this = "r from user: " + str(args_dict['r'])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -r " + str(args_dict['r'])
  ############### <end> rotation rate
  
  
  ############### <begin> Exposure
  print ("\n\n-E: Exposure time (seconds/frame).")
  print ("\tEMPIAR-10293    -> 0.644")
  print ("\tketone tutorial -> 1")
  
  if "E" not in args_dict:
    if (int(args_dict['sections']) > 1):
      combi = ('E', str(mrc_wo_path_wo_ext)) # assumes that input mrc/mrc is stack
    else: # if (int(args_dict['sections']) == 1):
      combi = ('E', str(mrc_wo_path_wo_ext_w_4_questions_marks)) # assumes that input mrc/mrc is single 2D images
    
    if (combi not in args_dict):
      args_dict[combi] = receive_from_user("E")
      
    write_this = "E from user: " + str(args_dict[combi])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -E " + str(args_dict[combi])
  else:
    write_this = "E from user: " + str(args_dict['E'])
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    command_for_mrc2smv = command_for_mrc2smv + " -E " + str(args_dict['E'])
  ############### <end> Exposure
  
  
  ############### <begin> Physical length of pixel
  print ("\n\n-P: Physical side length of a square pixel (mm)")
  print ("\tCetaD/Falcon III camera, Catalase/ketone tutorial -> 0.014")
  print ("\tOneView camera, EMPIAR-10293                      -> 0.015")
  if "P" not in args_dict:
    args_dict['P'] = receive_from_user("-P")
  write_this = "P from user: " + str(args_dict['P'])
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  command_for_mrc2smv = command_for_mrc2smv + " -P " + str(args_dict['P'])
  ############### <end> Physical length of pixel
  
  
  if (int(args_dict['sections']) == 1):
    command = command_for_mrc2smv + " -o " + str(output_folder_name)
    global_mrc_filename = mrc_w_path[:-9] + "_*.mrc"
    command = "\n" + command + "_####.img " + str(global_mrc_filename) + "\n"
  else:
    command = "\n" + command_for_mrc2smv + " -o " + str(output_folder_name) + "_####.img " + str(mrc_w_path) + "\n"
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  
  print_this = "\t(note) Overflows and underflows show violation of range during mrc to image file conversion. \
               Unless these violations are way too many, there is nothing to be concerned with."
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  ran_mrc2smv = False
  # if (platform.system() == "Linux"):
  #   if ('PNNL_HPC_Cascade_sbatch' in args_dict.keys()):
  #     if (args_dict['PNNL_HPC_Cascade_sbatch'] == "True"): 
  #       run_mrc2smv_by_tvips_at_PNNL_HPC_Cascade(args_dict['repo_location'], command)
  #       ran_mrc2smv = True
  if (ran_mrc2smv == False):
    print_this = "\t(note) mrc2smv of 2.4 GB mrc took ~30 seconds.\n"
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    os.system(command)
  
  end_time = time.time()
  
  write_this = util.show_time(process, start_time, end_time)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])

  return True
######### end of def run_mrc2smv_by_tvips(args_dict, mrc_w_path, output_folder_name)


def run_mrc2smv_by_tvips_at_PNNL_HPC_Cascade(repo_location, command):
  
  #open_this_template_file = str(repo_location) + "/templates/slurm_template_GPU"
  # 07/30/2020, pncc is very busy, can't run
  
  open_this_template_file = str(repo_location) + "/templates/slurm_template_emsls50432"
  
  f_in  = codecs.open(open_this_template_file, 'r')
  new_slurm_script_file_name = "slurm_mrc2smv"
  #f_out = codecs.open(new_slurm_script_file_name, 'wb') -> "TypeError: a bytes-like object is required, not 'str'" later
  f_out = codecs.open(new_slurm_script_file_name, 'w')
  for line in f_in:
    f_out.write(line)
  f_out.write(command)
  f_in.close()
  f_out.close()
  
  while (True):
    number_of_pending_or_active_jobs = subprocess.check_output(command_for_number_of_pending_or_active_jobs, shell=True)
    if (int(number_of_pending_or_active_jobs) < 12):
      launch_cascade_jobs(new_slurm_script_file_name)
      break # needed
    time.sleep(1)
  
  start_time_for_job = time.time()
  while (True):
    print ("\n\nStill, AutoMicroED needs to finish mrc2smv")
    end_time_for_job = time.time()
    print (util.show_time("Waiting seconds to launch a job so far", start_time_for_job, end_time_for_job))
    waiting(15)
    
    number_of_pending_or_active_jobs = subprocess.check_output(command_for_number_of_pending_or_active_jobs, shell=True)
    print ("\tnumber of pending or active jobs:" + str(number_of_pending_or_active_jobs.decode('utf-8')))
    if (int(number_of_pending_or_active_jobs) == 0):
      print ("no pending or active jobs")
      break
    
    number_of_pending_jobs = subprocess.check_output(command_for_number_of_pending_jobs, shell=True)
    number_of_active_jobs = subprocess.check_output(command_for_number_of_active_jobs, shell=True)
    print ("\tnumber of pending jobs:" + str(number_of_pending_jobs.decode('utf-8')))  
    print ("\tnumber of active jobs:" + str(number_of_active_jobs.decode('utf-8')))
    if (int(number_of_active_jobs) == 0):
      print ("cascade job is not launched yet")
      continue
    else:
      print ("cascade job is launched")
      print_this = "mrc2smv of 2.4 GB mrc took ~30 seconds\n"
      print (print_this)
      
      img_file_number = 0
      for img_file in glob.glob("*.img"):
        img_file_number += 1
      print ("Current img_file_number in img folder:" + str(img_file_number))
      
      if (img_file_number == 0):
        continue
      waiting(30)
      img_file_number_after_waiting = 0
      for img_file in glob.glob("*.img"):
        img_file_number_after_waiting += 1
      print ("Current img_file_number_after_waiting in img folder:" + str(img_file_number_after_waiting))
      
      if (img_file_number == img_file_number_after_waiting):
        break
######### end of def run_mrc2smv_by_tvips_at_PNNL_HPC_Cascade(logfile_name_w_abs_path, repo_location, mrc_w_path, output_folder_name)

'''
def run_mrc2smv_by_wcen(args_dict, mrc_w_path, output_folder_name):  
  process = "mrc2smv by wcen with " + str(mrc_w_path)
  util.show_header(process)
  start_time = time.time()

  mrc = util.load_density_file(mrc_w_path)

  print (f"mrc_w_path:{mrc_w_path}")

  print (f"mrc.data.shape:{mrc.data.shape}")
  # each mrc -> (2048, 2048)

  mrc_base_file_name = os.path.basename(mrc_w_path)

  out_tiff_path = mrc_base_file_name[:-4] + ".tiff"

  if os.path.isdir("tiff") == False:
    os.mkdir("tiff")
  out_tiff_path = os.path.join("tiff", out_tiff_path)

  tifffile.imsave( out_tiff_path, mrc.data )
#end of def run_mrc2smv_by_wcen(args_dict, mrc_w_path, output_folder_name):  
'''
