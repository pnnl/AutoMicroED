from datetime import datetime as dt
from math import isclose
import argparse, codecs, glob, os, platform, random, shutil, signal, subprocess, sys, time
import mrc2smv, protein, shelx, xds, xdsconv, xscale
import mrcfile

try:
  from envbash import load_envbash
except:
  print ("envbash not found, install it by typing")
  print ("\tpip install envbash")
  print ("\tReference: https://pypi.org/project/envbash/")
  exit(1)

try:
  import matplotlib.image as mpimg
except:
  print ("matplotlib not found, install it.")
  print ("\tconda install matplotlib")
  print ("\t\"python -m pip install -U matplotlib\" may also install matplotlib, but it may result in \"PermissionError...python3.6\" eventually")
  exit(1)
  
import numpy as np

home_dir_path = os.path.expanduser("~")
user_ID = os.path.basename(home_dir_path)

command_for_number_of_pending_or_active_jobs = "squeue | grep " + str(user_ID) + " | wc -l"
command_for_number_of_pending_jobs = "squeue | grep " + str(user_ID) + " | grep \" PD \" | wc -l"
command_for_number_of_active_jobs = "squeue | grep " + str(user_ID) + " | grep \" R \" | wc -l"



## <begin> writing print_this_for_movie_inspection
print_this = "Check the quality of the movies (*.mrc) by Fiji."
print_this = print_this + "\n\t(When open Fiji in macOS) Fiji can be installed in /Applications"
print_this = print_this + "\n\t(When ssh to one Linux machine by iterm2) ssh with -Y. (For example, ssh -Y kimd999@kriosgpu.emsl.pnl.gov)"
print_this = print_this + "\n\t(When ssh to one Linux machine by iterm2) ssh with -X doesn't work."
print_this = print_this + "\n\t(When ssh to one Linux machine by iterm2) Then, open Fiji. (For example, /msc/krios/bin/ImageJ-linux64)"

print_this = print_this + "\n\t(note) Adjust the contrast and brightness to see the diffraction spots (Image -> Adjust -> Brightness/Contrast -> Auto)."
print_this = print_this + "\n\t Pressing left and right arrow key will show more images at different z values."
print_this = print_this + "\n\t Specifically, distinct peaks in reciprocal space are ideal.\n\t On the other hand, if peaks are broad or duplicated, crystal might have been cracked or glued together."
print_this = print_this + "\n\t Adxv can also check the quality of the movies (*.mrc)."
print_this = print_this + "\n\t However, the Adxv seems not show more images at different z values."

print_this = print_this + "\n\nPress enter key once movie qualities are checked ok.\n"
print_this = print_this + "\t(note) Add \"Bypass_movie_inspection True\" in an argument file if a user wants to skip this manual check of input movie files.\n"
print_this_for_movie_inspection = print_this + "\t(note) Enter \"bypass\" now if a user wants to add \"Bypass_movie_inspection True\" in an argument file.\n"
## <end> writing print_this_for_movie_inspection


## <begin> writing print_this_for_image_inspection
print_this = "\n\nInspect images (*.img) by Adxv to make sure that the files were converted well."
print_this = print_this + "\n\t(macOS) Adxv can be installed in /Applications"
print_this = print_this + "\n\t\t(when ssh to Linux machine by iterm2) In order to open Adxv in user's computer rather than Linux machine itself, a user needs to ssh with either -X or -Y. ssh with -XC doesn't work"
print_this = print_this + "\n\t\t(when ssh to Linux machine by iterm2) For example, ssh -X kimd999@kriosgpu.emsl.pnl.gov works. However, ssh -XC kimd999@kriosgpu.emsl.pnl.gov doesn't work"
print_this = print_this + "\n\t\t(when ssh to Linux machine by x11-x-term) In order to open Adxv in user's computer rather than Linux machine itself, a user needs to ssh with -Y only. ssh with -XC or -X doesn't work"
print_this = print_this + "\n\t\t(when ssh to Linux machine by x11-x-term)\nFor example, ssh -Y kimd999@kriosgpu.emsl.pnl.gov works."
print_this = print_this + "\n\t(after ssh to Linux machine) Launch adxv (For example, cd /opt/apps/bin then ./adxv.x86_64CentOS7"
print_this = print_this + "\nThese result image files (*.img) are in output/<date-time of launching this job>/<mrc file list prefix>/img"

print_this = print_this + "\nJust press enter key once images are inspected.\n"
print_this = print_this + "\t(note) Add \"Bypass_image_inspection True\" in an argument file if a user wants to skip this manual check.\n"
print_this_for_image_inspection = print_this + "\t(note) Enter \"bypass\" now if a user wants to add \"Bypass_image_inspection True\" in an argument file.\n"
## <end> writing print_this_for_image_inspection


message_for_CORRECT_LP_not_found = \
'''That was a final troubleshooting.
    CORRECT.LP still not found.
    
    Most likely solution ->
    If a user used raw mrc file (e.g. 4096x4096), xds sometimes can't find a solution.
    The issue with the full size MRCS datasets was that the peak intensities were too low for higher resolution reflections and binning takes a 2x2 pixel area and makes it a single pixel which boost the relative signal versus background. I think at full size the signal was just too disperse for XDS to find a reliable lattice.
    Therefore, consider to bin input mrc first. This binning can be done with \"newstack -bin 2 <raw mrc filename> <new mrc filename>\"
    If binned (downsampled), multiply by 2 for P and divide by 2 for NX, NY
    
    Other possible solutions ->
    "IF THE BEST SOLUTION IS REALLY NONSENSE YOU SHOULD FIRST HAVE
    A LOOK AT THE ASCII-FILE "SPOT.XDS". THIS FILE CONTAINS THE
    INITIAL SPOT LIST SORTED IN DECREASING SPOT INTENSITY. SPOTS
    NEAR THE END OF THE FILE MAY BE ARTEFACTS THAT CAN BE ERASED.
    ALTERNATIVELY YOU MAY TRY DIFFERENT VALUES FOR "INDEX_ORIGIN"
    AS SUGGESTED IN THE ABOVE LISTING.
    IF THE CRYSTAL HAS SLIPPED AT THE BEGINNING OF DATA COLLECTION, YOU MAY CHOOSE TO SKIP SOME OF THE FIRST FRAMES BY CHANGING THE "DATA_RANGE=" IN FILE "XDS.INP" AND START ALL OVER AGAIN."
    
    
    (Possible cause #1) xds executable might be broken like "forrtl: No such file or directory" 
    
    (Possible cause #2) xds executable may have expired license like
    "Sorry, license expired on 31-Mar-2021".
    
    Both causes were solved by overwriting existing binaries with newly downloaded ones.
      Re-download xds executable by
    
      (in Linux)
      --no-check-certificate -O- https://xds.mr.mpg.de/XDS-INTEL64_Linux_x86_64.tar.gz | tar xzvf -
      or
      wget https://xds.mr.mpg.de/XDS-INTEL64_Linux_x86_64.tar.gz
      
      (in MacOS)
      wget https://xds.mr.mpg.de/XDS-OSX_64.tar.gz
      
    Other case -> Using too few number of images (like < 10) failed to generate CORRECT.LP
    Other case -> When Doo Nam entered wrong r or voltage value intentionally, this failture happened.
    Other case -> When Doo Nam excluded certain frames in xds intentionally, this failture happened.'''
    

class LoadFromFile (argparse.Action):
  def __call__ (self, parser, namespace, values, option_string = None):
    with values as f:
      parser.parse_args(f.read().split(), namespace)


def add_args_from_file(parser, args_file):
  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
  parser.add_argument('-f')
  this = '@' + str(args_file)
  print ("this:" + str(this))
  parser.parse_args(['-f', 'foo', this])
  return parser
######## end of def add_args_from_file(args_file_name):


class AlarmException(Exception):
  pass


def alarmHandler(signum, frame):
  raise AlarmException  


def args_file_parse(args_dict):
  f_in  = codecs.open(args_dict['args_file_w_abs_path'], 'r')
  for line in f_in:
    splited_line = line.split()
    if (len(splited_line) < 2):
      continue
    elif (splited_line[0] == "B"):
      args_dict['B'] = splited_line[1]
    elif (splited_line[0] == "Bypass_generate_adx_inspection"):
      args_dict['Bypass_generate_adx_inspection'] = splited_line[1]
    elif (splited_line[0] == "Bypass_image_inspection"):
      args_dict['Bypass_image_inspection'] = splited_line[1]
    
    elif (splited_line[0] == "Bypass_movie_inspection"):
      args_dict['Bypass_movie_inspection'] = splited_line[1]
    
    # spot2pdb should run always (Sam)
    # elif (splited_line[0] == "Bypass_spot2pdb_inspection"):
    #   args_dict['Bypass_spot2pdb_inspection'] = splited_line[1]
    
    elif (splited_line[0] == "ccp4_folder"):
      args_dict['ccp4_folder'] = splited_line[1]
    
    elif (splited_line[0] == "columns"):
      args_dict['columns'] = splited_line[1]

    elif (splited_line[0] == "COMPOSITION_PROTEIN_SEQUENCE"):
      args_dict['COMPOSITION_PROTEIN_SEQUENCE'] = os.path.join(args_dict['starting_dir'], splited_line[1])
      if (os.path.exists(args_dict['COMPOSITION_PROTEIN_SEQUENCE']) == False):
        print_this = str(args_dict['COMPOSITION_PROTEIN_SEQUENCE']) + " doesn't exist."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
        return False
    
    elif (splited_line[0] == "COMPOSITION_PROTEIN_SEQUENCE_NUM"):
      args_dict['COMPOSITION_PROTEIN_SEQUENCE_NUM'] = splited_line[1]
    elif (splited_line[0] == "d_calibrated"): # true DETECTOR_DISTANCE
      if (len(splited_line) < 3):
        args_dict['d_calibrated'] = splited_line[1]
      else:
        combi = ('d_calibrated', str(splited_line[1]))
        args_dict[combi] = splited_line[2]
    elif (splited_line[0] == "d_calibration_coef"):
      args_dict['d_calibration_1st_coef'] = splited_line[1]
      args_dict['d_calibration_2nd_coef'] = splited_line[2]
    elif (splited_line[0] == "d_not_calibrated"): # DETECTOR_DISTANCE_from_Krios
      if (len(splited_line) == 3):
        combi = ('d_not_calibrated', str(splited_line[1]))
        args_dict[combi] = splited_line[2]
      else:
        args_dict['d_not_calibrated'] = splited_line[1]
    elif (splited_line[0] == "E"):
      if (len(splited_line) == 3):
        combi = ('E', str(splited_line[1]))
        args_dict[combi] = splited_line[2]
      else:
        args_dict['E'] = splited_line[1]

    elif (splited_line[0] == "ENSEMBLE_PDBFILE"):
      args_dict['ENSEMBLE_PDBFILE'] = os.path.join(args_dict['starting_dir'], splited_line[1])

      if (os.path.exists(args_dict['ENSEMBLE_PDBFILE']) == False):
        print_this = str(args_dict['ENSEMBLE_PDBFILE']) + " doesn't exist."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
        return False

    elif (splited_line[0] == "ENSEMBLE_PDBFILE_IDENTITY"):
      args_dict['ENSEMBLE_PDBFILE_IDENTITY'] = splited_line[1]

    elif (splited_line[0] == "EXCLUDE_DATA_RANGE"):
      #print (f"len(splited_line):{len(splited_line)}")
      #4
      if (len(splited_line) < 3):
        continue
      elif (len(splited_line) == 3):
        write_this = "If a user wants to exclude 1/single frame, specify like 'EXCLUDE_DATA_RANGE 13 13' in args_file. Refer http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_parameters.html#EXCLUDE_DATA_RANGE="
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        return False
      elif (len(splited_line) > 3):
        write_this = "EXCLUDE_DATA_RANGE=" + str(splited_line[2]) + " " + str(splited_line[3])
        args_dict['EXCLUDE_DATA_RANGE', str(splited_line[1])] = write_this

      print (f"args_dict:{args_dict}")
      #('EXCLUDE_DATA_RANGE', '112002_????'): 'EXCLUDE_DATA_RANGE=1 5'
      #print_this = "\nPress enter to continue.\n"
      #input(print_this) 


    elif (splited_line[0] == "generate_adx_folder"):
      if (os.path.isdir(splited_line[1]) == False):
        print_this = splited_line[1] + " doesn't exist. Please correct generate_adx_folder."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        exit(1)
      args_dict['generate_adx_folder'] = splited_line[1]

    elif (splited_line[0] == "Generate_LATT_SYMM_from_website"):
      args_dict['Generate_LATT_SYMM_from_website'] = splited_line[1]
    
    
    elif ((splited_line[0] == "INCLUDE_RESOLUTION_RANGE") or (line[:25] == "INCLUDE_RESOLUTION_RANGE=")):
      args_dict['INCLUDE_RESOLUTION_RANGE'] = '' # this is needed
      for i in range(len(splited_line)):
        if (i == 0):
          continue
        args_dict['INCLUDE_RESOLUTION_RANGE'] = args_dict['INCLUDE_RESOLUTION_RANGE'] + splited_line[i] + " "
    elif (splited_line[0] == "least_completeness_overall"):
      args_dict['least_completeness_overall'] = splited_line[1]
    
    elif (splited_line[0] == "mrc2smv_folder"):
      if (os.path.isdir(splited_line[1]) == False):
        print_this = splited_line[1] + " doesn't exist. Please correct mrc2smv_folder."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        exit(1)
      args_dict['mrc2smv_folder'] = splited_line[1]

    elif (splited_line[0] == "multi_core_xds"):
      args_dict['multi_core_xds'] = splited_line[1]
      
    elif (splited_line[0] == "NX"):
      args_dict['NX'] = splited_line[1]

    elif (splited_line[0] == "NY"):
      args_dict['NY'] = splited_line[1]

    elif (splited_line[0] == "ORGX"):
      if (len(splited_line) > 2):
        # do not specify as '(len(splited_line) == 3)' because there could be additional workds like #~~~
        args_dict['ORGX', str(splited_line[1])] = splited_line[2]
      else:
        args_dict['ORGX'] = splited_line[1]

    elif (splited_line[0] == "ORGY"):
      if (len(splited_line) > 2):
        args_dict['ORGY', str(splited_line[1])] = splited_line[2]
      else:
        args_dict['ORGY'] = splited_line[1]
    
    elif (splited_line[0] == "outdir"):
      args_dict['outdir'] = splited_line[1]

    elif (splited_line[0] == "P"):
      args_dict['P'] = splited_line[1]
    
    elif (splited_line[0] == "PNNL_HPC_Cascade_sbatch"):
      args_dict['PNNL_HPC_Cascade_sbatch'] = splited_line[1]
    
    elif (splited_line[0] == "protein"):
      args_dict['protein'] = splited_line[1]

    elif (splited_line[0] == "r"):
      if (len(splited_line) == 3):
        combi = ('r', str(splited_line[1]))
        args_dict[combi] = splited_line[2]
      else:
        args_dict['r'] = splited_line[1]

    elif (splited_line[0] == "remove_HETATM"):
      args_dict['remove_HETATM'] = splited_line[1]

    elif ((splited_line[0] == "ROTATION_AXIS") or (line[:14] == "ROTATION_AXIS=")):
      args_dict['ROTATION_AXIS'] = '' # this is needed
      for i in range(len(splited_line)):
        if (i == 0):
          continue
        args_dict['ROTATION_AXIS'] = args_dict['ROTATION_AXIS'] + splited_line[i] + " "

    elif (splited_line[0] == "sections"):
      args_dict['sections'] = splited_line[1]

    elif (splited_line[0] == "SFAC"):
      args_dict['SFAC'] = ''  # this is needed
      for i in range(len(splited_line)):
        if (i == 0):
          continue
        args_dict['SFAC'] = args_dict['SFAC'] + splited_line[i] + " "

    elif (splited_line[0] == "SEARCH_ENSEMBLE_NUM"):
      args_dict['SEARCH_ENSEMBLE_NUM'] = splited_line[1]

    # in args_file_parse
    elif (splited_line[0] == "SPACE_GROUP_NUMBER"):
      args_dict['SPACE_GROUP_NUMBER'] = splited_line[1]
    
    elif (splited_line[0] == "spot2pdb_folder"):
      args_dict['spot2pdb_folder'] = splited_line[1]

    elif (splited_line[0] == "spot2pdb_RESOLUTION_RANGE"):
      args_dict['spot2pdb_RESOLUTION_RANGE_min'] = splited_line[1]
      args_dict['spot2pdb_RESOLUTION_RANGE_max'] = splited_line[2]

    elif (splited_line[0] == "STARTING_ANGLE"):
      if len(splited_line) == 3:
        args_dict['STARTING_ANGLE', str(splited_line[1])] = splited_line[2]
      else:
        args_dict['STARTING_ANGLE'] = splited_line[1]
    
    elif (splited_line[0] == "TEST_RESOLUTION_RANGE"):
      args_dict['TEST_RESOLUTION_RANGE_max'] = splited_line[1]
      args_dict['TEST_RESOLUTION_RANGE_min'] = splited_line[2]
      
    elif (splited_line[0] == "TRUSTED_REGION"):
      args_dict['TRUSTED_REGION_min'] = splited_line[1]
      args_dict['TRUSTED_REGION_max'] = splited_line[2]
      
    elif (line[:15] == "TRUSTED_REGION="):
      splited_line_by_equal = line.split("=")
      splited_line_for_final = splited_line_by_equal[1].split()
      args_dict['TRUSTED_REGION_min'] = splited_line_for_final[0]
      args_dict['TRUSTED_REGION_max'] = splited_line_for_final[1].split("\n")[0]
    
    elif (splited_line[0] == "UNIT"):
      args_dict['UNIT'] = '' # this is needed
      for i in range(len(splited_line)):
        if (i == 0):
          continue
        args_dict['UNIT'] = args_dict['UNIT'] + splited_line[i] + " "
    
    elif (splited_line[0] == "UNIT_CELL_CONSTANTS"):
      args_dict['UNIT_CELL_CONSTANTS'] = ''
      for i in range(len(splited_line)):
        if (i == 0):
          continue
        args_dict['UNIT_CELL_CONSTANTS'] = args_dict['UNIT_CELL_CONSTANTS'] + splited_line[i] + " "
      
      # print (args_dict)
      # print_this = "\nPress enter to continue.\n"
      # input(print_this)

    elif (splited_line[0] == "voltage_of_the_microscope"):
      args_dict['voltage_of_the_microscope'] = splited_line[1]

    elif (splited_line[0] == "X-RAY_WAVELENGTH"):
      args_dict['X-RAY_WAVELENGTH'] = splited_line[1]
  f_in.close()

  ### <begin> hook
  if "SPACE_GROUP_NUMBER" in args_dict:
    if str(args_dict['SPACE_GROUP_NUMBER']) != "0":
      if "UNIT_CELL_CONSTANTS" not in args_dict:
        print_this = "SPACE_GROUP_NUMBER is specified in args_file, but UNIT_CELL_CONSTANTS is not."
        print_this = print_this + "\nIf a user specifies SPACE_GROUP_NUMBER in args_file, then the person needs to specify UNIT_CELL_CONSTANTS as well (this is XDS requirement)."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
        return False
  ### <end> hook

  return args_dict
######## end of def args_file_parse(args_file_name):


def check_movie_quality():
  print (print_this_for_movie_inspection)
  '''
  if ("kimd999" in home_dir_path):
    nonBlockingRawInput(python_version, print_this)
  else:
    input(print_this)'''
  bypass_can = input()
  
    
  if (bypass_can.rstrip() == "bypass"):
    f_out = codecs.open("../../args_file_generated_by_AutoMicroED.txt", 'a')
    write_this = "Bypass_movie_inspection True # generated by AutoMicroED\n"
    f_out.write(write_this)
    f_out.close()
######### end of def check_movie_quality()


def closing_remark(args_dict):
  flog         ("See https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md#spot2pdb to know how to analyze spot2pdb result.\n", args_dict['logfile_name_w_abs_path'])
  flog_wo_print("See https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md#spot2pdb to know how to analyze spot2pdb result.\n", args_dict['summary_logfile_name_w_abs_path'])

  if (
     (str(args_dict['protein']).upper() == "FALSE") 
     or (str(args_dict['protein']).upper() == "F") 
     ):    
    flog("\nSee https://github.com/pnnl/AutoMicroED/blob/master/reference/analyze_small_molecule_result.md to know how to analyze result.\n", args_dict['logfile_name_w_abs_path'])
    flog_wo_print("See https://github.com/pnnl/AutoMicroED/blob/master/reference/analyze_small_molecule_result.md to know how to analyze result.", args_dict['summary_logfile_name_w_abs_path'])
  else:
    flog("\nSee https://github.com/pnnl/AutoMicroED/blob/master/reference/analyze_protein_result.md to know how to analyze result.\n", args_dict['logfile_name_w_abs_path'])
    flog_wo_print("See https://github.com/pnnl/AutoMicroED/blob/master/reference/analyze_protein_result.md to know how to analyze result.", args_dict['summary_logfile_name_w_abs_path'])
######### end of def closing_remark()
  

def count_columns_sections_in_each_mrc_file_by_mrcfile(args_dict, mrc_w_path):
  mrc = load_density_file(mrc_w_path)
  print (f"mrc.data.shape:{mrc.data.shape}") ##(120, 2048, 2048)
  columns = mrc.data.shape[1]
  sections = mrc.data.shape[0]
  print ("columns: " + str(columns)) #2048
  print ("sections: " + str(sections)) # 120
  
  return columns, sections
######## end of count_columns_sections_in_each_mrc_file_by_mrcfile(args_dict, mrc_w_path):  


def file_size(fname):
    statinfo = os.stat(fname)
    return statinfo.st_size
########## end of file_size()


def flog(msg, outfile):
    msg = '{}     {}'.format(dt.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(msg)
    sys.stdout.flush()
    try:
        with codecs.open(outfile,'a') as f:
            f.write(msg+'\n')
    except Exception as e:
        log(e)
####### end of def flog(msg, outfile):


def flog_wo_print(msg, outfile):
    msg = '{}     {}'.format(dt.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    sys.stdout.flush()
    try:
        with codecs.open(outfile,'a') as f:
            f.write(msg+'\n')
    except Exception as e:
        log(e)
####### end of def flog(msg, outfile):

 
def generate_each_similar_UNIT_CELL_folder(args_dict):
  process = "generate each_similar_UNIT_CELL folder\n"
  flog(process, args_dict['logfile_name_w_abs_path'])
  starting_dir_in_this_fn = os.getcwd()
  print ("starting_dir_in_this_fn:" + str(starting_dir_in_this_fn))
  
  f_in = codecs.open("For_this_SPACE_GROUP_merge_these_HKL_by_xscale.txt", "r")
  # this file should consider space group only, not unit cell yet
  
  for line in f_in:
    XSCALE_LP_w_path = os.path.join("..", line.rstrip(), "XSCALE.LP")
    UNIT_CELL_CONSTANTS = retrieve_UNIT_CELL_CONSTANTS(args_dict, XSCALE_LP_w_path)
    # xscale merges many XDS_ASCII.HKL files from same SPACE_GROUP_NUMBER and similar UNIT_CELL_CONSTANTS
    print_this = "\tUNIT_CELL_CONSTANTS:" + str(UNIT_CELL_CONSTANTS)
    flog(print_this, args_dict['logfile_name_w_abs_path'])

    splited_UNIT_CELL_CONSTANTS = UNIT_CELL_CONSTANTS.split()
    
    a = splited_UNIT_CELL_CONSTANTS[0]
    b = splited_UNIT_CELL_CONSTANTS[1]
    c = splited_UNIT_CELL_CONSTANTS[2]
    alpha = splited_UNIT_CELL_CONSTANTS[3]
    beta = splited_UNIT_CELL_CONSTANTS[4]
    gamma = splited_UNIT_CELL_CONSTANTS[5] 
    new_folder_name = "a_" + str(a) + "_b_" + str(b) + "_c_" + str(c) + "_alpha_" + str(alpha) + "_beta_" + str(beta) + "_gamma_" + str(gamma)
     
    close_enough_already = False
    for entry in os.scandir('.'):
      if not entry.name.startswith('.') and entry.is_dir():
        a_from_folder_name = entry.name.split("_")[1]
        if (isclose(float(a_from_folder_name), float(a), abs_tol=1) == True):
          b_from_folder_name = entry.name.split("_")[3]
          if (isclose(float(b_from_folder_name), float(b), abs_tol=1) == True):
            c_from_folder_name = entry.name.split("_")[5]
            if (isclose(float(c_from_folder_name), float(c), abs_tol=1) == True):
              alpha_from_folder_name = entry.name.split("_")[7]
              if (isclose(float(alpha_from_folder_name), float(alpha), abs_tol=1) == True):
                beta_from_folder_name = entry.name.split("_")[9]
                if (isclose(float(beta_from_folder_name), float(beta), abs_tol=1) == True):
                  gamma_from_folder_name = entry.name.split("_")[11]
                  if (isclose(float(gamma_from_folder_name), float(gamma), abs_tol=1) == True):
                    close_enough_already = True
                    os.chdir(entry.name)
                    f_out = codecs.open("For_this_SPACE_GROUP_and_UNIT_CELL_merge_these_HKL_by_xscale.txt", "a")
                    f_out.write(line)
                    f_out.close()
                    break
        
    if (close_enough_already == False):
      os.mkdir(new_folder_name)
      os.chdir(new_folder_name)
      
      write_this = "\tFor UNIT_CELL " + str(new_folder_name) + ", merge these HKL data."
      flog(write_this, args_dict['logfile_name_w_abs_path'])
      flog(write_this, args_dict['summary_logfile_name_w_abs_path'])

      f_out = codecs.open("For_this_SPACE_GROUP_and_UNIT_CELL_merge_these_HKL_by_xscale.txt", "a")
      f_out.write(line)
      
      write_this = "\t\t" + str(line)
      flog(write_this, args_dict['logfile_name_w_abs_path'])
      flog(write_this, args_dict['summary_logfile_name_w_abs_path'])
      
      f_out.close()    
    os.chdir(starting_dir_in_this_fn)
    
  f_in.close()
#################### end of def generate_each_similar_UNIT_CELL_folder(logfile_name_w_abs_path)


def generate_each_SPACE_GROUP_folder(args_dict):
  starting_dir = os.getcwd()
  
  process = "generate each_SPACE_GROUP folder\n"
  flog(process, args_dict['logfile_name_w_abs_path'])
  
  all_immediate_sub_dir = next(os.walk('.'))[1]
  
  if args_dict['more_crystal_needed'] == True:
    if (len(all_immediate_sub_dir) < 2):
      flog("There is only 1 crystal.\nTherefore, there are no more crystals to merge.\nConsider to add more crystal information.", \
           args_dict['logfile_name_w_abs_path'])
      return False
    
  SPACE_GROUP_NUMBER_array = []
  combi_array = []
  for i in range(len(all_immediate_sub_dir)):
      sub_dir = os.path.join(all_immediate_sub_dir[i], "xds")
      source_file = os.path.join(sub_dir, "XSCALE.LP")
      SPACE_GROUP_NUMBER = retrieve_SPACE_GROUP_NUMBER(args_dict, source_file)
      SPACE_GROUP_NUMBER_array.append(SPACE_GROUP_NUMBER)
      combi = (str(SPACE_GROUP_NUMBER), str(sub_dir))
      combi_array.append(combi)
  
  SPACE_GROUP_NUMBER_array_unique = np.unique(SPACE_GROUP_NUMBER_array)
  write_this = "unique SPACE_GROUP_NUMBERs:" + str(SPACE_GROUP_NUMBER_array_unique)

  flog(write_this, args_dict['logfile_name_w_abs_path'])
  flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])

  for i in range(len(SPACE_GROUP_NUMBER_array_unique)):
    unique_SPACE_GROUP_NUMBER = SPACE_GROUP_NUMBER_array_unique[i]
    if str(unique_SPACE_GROUP_NUMBER) == "False":
      write_this = "'False' is returned as unique_SPACE_GROUP_NUMBER. Therefore, skip this/these data belong to False SPACE_GROUP."
      flog(write_this, args_dict['logfile_name_w_abs_path'])
      flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])  
      continue

    folder_name = "SPACE_GROUP_" + str(unique_SPACE_GROUP_NUMBER)

    os.mkdir(folder_name)
    os.chdir(folder_name)
    
    write_this = "For " + str(folder_name) + ", merge these data."
    flog(write_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
    
    list_f = codecs.open("For_this_SPACE_GROUP_merge_these_HKL_by_xscale.txt", "w")
    for j in range(len(combi_array)):
      if (combi_array[j][0] == unique_SPACE_GROUP_NUMBER):
        cp_from_here = str(combi_array[j][1])
        
        write_this = "\t\t" + str(cp_from_here) + "\n"
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        flog(write_this, args_dict['summary_logfile_name_w_abs_path'])
        
        list_f.write(str(combi_array[j][1]) + "\n")
    list_f.close()
    
    os.chdir(starting_dir)
#################### end of def generate_each_SPACE_GROUP_folder(logfile_name_w_abs_path)


def launch_cascade_jobs(new_slurm_script_file_name):
  command = "\nsbatch " + str(new_slurm_script_file_name)
  print (command)
  os.system(command)
########## end of def launch_cascade_jobs(new_slurm_script_file_name):


def load_density_file(fname):
    """load a .mrc file using the mrcfile package

    Args:
        fname ([str]): filename / filepath

    Returns:
        [mrcfile object]: MRC data 
    """ 
    # load .mrc tomogram file as a MRC object which has header and data properties. 
    # see: https://mrcfile.readthedocs.io/en/latest/usage_guide.html 
    mrc = mrcfile.mmap(fname, mode=u'r')  # memory mapped mode for large files
    #print(f"mrc.is_image_stack():{mrc.is_image_stack()}")  # check if mrc is an image stack 
    #print(f"mrc.is_volume():{mrc.is_volume()}")  # check if mrc is a volume
    return mrc
##### end of def load_density_file(fname):


def mrc2png(args_dict, ORGX_ORGY, mrc_w_path):
  mrc_wo_path = os.path.basename(mrc_w_path)
  mrc_wo_path_wo_ext = os.path.splitext(mrc_wo_path)[0]
  
  cwd = os.getcwd()
  target_folder = os.path.join(cwd[:(len(cwd)-3)], "img")
  output_file_name = os.path.join(target_folder, mrc_wo_path_wo_ext)
  
  if (mrc_w_path[len(mrc_w_path)-5:len(mrc_w_path)] == ".mrcs"):
    mrcs = True
  else:
    mrcs = False
  
  if (mrcs == True):
    output_file_name = output_file_name + "_mrcs.png"
  else:
    output_file_name = output_file_name + "_mrc.png"
  
  if (ORGX_ORGY == "ORGX"):
    print_this = "\tAutoMicroED will transform " + str(mrc_w_path) + " to png file(s)."
    flog(print_this, args_dict['logfile_name_w_abs_path'])

    command = "e2proc2d.py " + str(mrc_w_path) + " " + str(output_file_name) \
    + " --outmode uint8 --unstacking\n"
    flog(command, args_dict['logfile_name_w_abs_path'])
    os.system(command)
  
  search_this = os.path.join(target_folder, "*.png")
  
  for png_name in glob.glob(search_this): # this glob pick file randomly
    base_png_name = os.path.basename(png_name)
    splited_base_png_name = base_png_name.split(".png")
    splited_base_png_name2 = splited_base_png_name[0].split("-")
    image_num = int(splited_base_png_name2[len(splited_base_png_name2)-1])
    
    if (int(args_dict['sections'])) > 1:
      if (image_num <= args_dict['min_DATA_RANGE']) or (image_num >= args_dict['max_DATA_RANGE']):
        continue
  
    print_this = "png file that is ultimately used for estimate_ORGX_ORGY_by_AutoMicroED:" + str(png_name)
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    return png_name
############ end of def mrc2png(ORGX_ORGY, mrc_w_path, logfile_name_w_abs_path):


def nonBlockingRawInput(python_version, prompt='', timeout=1): # timeout should be integer, not float
  print_this = "\n\tContinuing..."
  print (print_this)
###### end of def nonBlockingRawInput(prompt='', timeout=2)


def per_each_mrc_file_both_single_and_multiple_sections (args_dict, mrc_w_path, output_folder_name):

  print (f"mrc_w_path:{mrc_w_path}")
  # for smv only mrc_w_path is not accurate (uses just last one)
  # tutorial -> /gpustorage/MicroEDProc/SMP/combogrid_061521/2021-06-15-165749/165749merged.mrcs
  # smv only -> /gpustorage/DN/microED/small/acet/protein_False/tutorial/output/keep_20210917_15_15_10/archive/170629merged/img

  print (f"output_folder_name:{output_folder_name}")
  # tutorial -> 165749merged
  # smv only -> 165749merged

  if (args_dict['input_list_has_mrc'] == True):
    write_this = "\nInput mrc to process: " + str(mrc_w_path)
    flog(write_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])

    return_of_run_mrc2smv = mrc2smv.run_mrc2smv(args_dict, mrc_w_path, output_folder_name)
    if (return_of_run_mrc2smv == -999):
      return -999
  else:
    mrc2smv.prepare_d_calibrated(args_dict, output_folder_name)

  args_dict['min_DATA_RANGE'], args_dict['max_DATA_RANGE'] \
  = mrc2smv.remove_first_and_last_image_files(output_folder_name)
    
  # Irina prefers to remove first 2 and last 2 frames
  args_dict['min_DATA_RANGE'] = int(args_dict['min_DATA_RANGE']) + 1
  args_dict['max_DATA_RANGE'] = int(args_dict['max_DATA_RANGE']) - 1
  
  if ('Bypass_image_inspection' not in args_dict.keys()) \
      or (str(args_dict['Bypass_image_inspection']).upper() == "FALSE")\
      or (str(args_dict['Bypass_image_inspection']).upper() == "F"):
    print (print_this_for_image_inspection)
    bypass_can = input()
    if (bypass_can.rstrip() == "bypass"):
      f_out = codecs.open("args_file_generated_by_AutoMicroED.txt", 'a')
      write_this = "Bypass_image_inspection True # generated by AutoMicroED\n"
      f_out.write(write_this)
      f_out.close()
  
  # (devel) because of NAME_TEMPLATE_OF_DATA_FRAMES=/home/kimd999/auto_cryoEM/microED/tuto/output/20210603_23_6_19/20190913-162354/img/20190913-162354_????.img
  # run_xds runs as if input mrc_file still has multiple frames
  returned_from_run_xds = xds.run_xds(args_dict, mrc_w_path, output_folder_name)
  if (returned_from_run_xds == -999):
    return -999
  
  elif (returned_from_run_xds == "CORRECT.LP not found"):
    return "CORRECT.LP not found"

  elif (returned_from_run_xds == False):
    return "Running xds failed."


  ############# <begin> generate_adx
  if ('generate_adx_folder' not in args_dict.keys()):
    print_this = "\ngenerate_adx_folder is not defined in args_file\n"
    print_this = print_this + "Either specify it args_file (for later AutoMicroED run, for example, /opt/apps/AutoMicroED)"
    print_this = print_this + "\nor enter a full PATH of generate_adx now."
    print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt for an example of generate_adx_folder specification."
    print_this = print_this + "\n\tRefer https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md to know how to compile generate_adx"
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    generate_adx_folder = receive_from_user("generate_adx_folder")
    args_dict['generate_adx_folder'] = generate_adx_folder

  print_this = "generate_adx_folder:" + str(args_dict['generate_adx_folder'])
  flog(print_this, args_dict['logfile_name_w_abs_path'])

  command_for_generate_adx = str(os.path.join(str(args_dict['generate_adx_folder']), str("generate_adx")))
  if (os.path.exists(command_for_generate_adx) == False):
    print_this = str(command_for_generate_adx) + " doesn't exist."
    print_this = print_this + "\n\tRefer https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md to know how to compile generate_adx"
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
    return "failed"

  flog(command_for_generate_adx, args_dict['logfile_name_w_abs_path'])
  os.system(command_for_generate_adx)

  print_this = "generate_adx is ran"
  flog(print_this, args_dict['logfile_name_w_abs_path'])

  print_this = "Refer https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md to know how to analyze."
  flog(print_this, args_dict['logfile_name_w_abs_path'])


  ######### <begin> manual checking of generate_adx
  if ('Bypass_generate_adx_inspection' not in args_dict.keys()) \
      or (str(args_dict['Bypass_generate_adx_inspection']).upper() == "FALSE")\
      or (str(args_dict['Bypass_generate_adx_inspection']).upper() == "F"):

    print_this = "\n\t(note) Add \"Bypass_generate_adx_inspection True\" in an argument file if a user wants to skip this manual verification of indexing (xds result).\n"
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    print_this = "\nPress enter if this dataset looks ok.\n"
    
    # if ("kimd999" in home_dir_path):
    #   nonBlockingRawInput(print_this)
    # else:
    input(print_this)
  ######## <end> manual checking of generate_adx
  ############# <end> generate_adx


  
  ############# <begin> spot2pdb
  if ('spot2pdb_folder' not in args_dict.keys()):
    print_this = "\nspot2pdb_folder is not defined in args_file\n"
    print_this = print_this + "Either specify it args_file (for later AutoMicroED run, for example /opt/apps/AutoMicroED)"
    print_this = print_this + "\nor enter a full PATH of spot2pdb now."
    print_this = print_this + "\n\tsee (git repo)/templates/args_file/explanation_of_args.txt for an example of spot2pdb_folder"
    #print_this = print_this + "\n\t(note) Add \"Bypass_spot2pdb_inspection True\" in an argument file if a user wants to skip this manual check of spot2pdb result.\n"
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    spot2pdb_folder = receive_from_user("spot2pdb_folder")
    args_dict['spot2pdb_folder'] = spot2pdb_folder


  print_this = "spot2pdb_folder:" + str(args_dict['spot2pdb_folder'])
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  command_for_spot2pdb = str(os.path.join(str(args_dict['spot2pdb_folder']), str("spot2pdb")))

  if ('protein' not in args_dict.keys()):
    protein = receive_from_user("protein")
    args_dict['protein'] = protein


  command_for_spot2pdb = command_for_spot2pdb + " -q " + str(args_dict['spot2pdb_RESOLUTION_RANGE_max']) \
      + " -r " + str(args_dict['spot2pdb_RESOLUTION_RANGE_min'])

  '''
  if ((str(args_dict['protein']) == "FALSE") or (str(args_dict['protein']) == "False") \
    or (str(args_dict['protein']) == "false")):
      command_for_spot2pdb = command_for_spot2pdb + " -q 4 -r 0.5"
  else:
    print_this = "Since target is protein, 6~999 Angstrom resolution will be assigned to spot2pdb"
    flog(print_this, args_dict['logfile_name_w_abs_path'])
  '''

  flog(command_for_spot2pdb, args_dict['logfile_name_w_abs_path'])
  os.system(command_for_spot2pdb)

  print_this = "spot2pdb is ran.\n"
  flog(print_this, args_dict['logfile_name_w_abs_path'])

  

  '''
  base_folder_name = os.path.basename(os.getcwd())

  command = "cp SPOT-indexed.pdb " + "SPOT-indexed_" + str(base_folder_name) + ".pdb"
  flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)

  command = "cp SPOT-notindexed.pdb " + "SPOT-notindexed_" + str(base_folder_name) + ".pdb"
  flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)

  print_this = "(Just in case that a user runs AutomicroED in a remote computer) To help easier scp/rsync of SPOT-indexed.pdb and SPOT-notindexed.pdb to user's computer"
  print_this = print_this + " AutoMicroED copied/renamed SPOT-indexed.pdb and SPOT-notindexed.pdb according to folder name."
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  '''
  
  print_this = "Refer https://github.com/pnnl/AutoMicroED/blob/master/reference/protocol.md#spot2pdb to visualize with coot"
  flog(print_this, args_dict['logfile_name_w_abs_path'])

  '''
  ######### <begin> manual check of spot2pdb
  if ('Bypass_spot2pdb_inspection' not in args_dict.keys()) \
      or (str(args_dict['Bypass_spot2pdb_inspection']).upper() == "FALSE")\
      or (str(args_dict['Bypass_spot2pdb_inspection']).upper() == "F"):

    print_this = "\n\t(note) Add \"Bypass_spot2pdb_inspection True\" in an argument file if a user wants to skip this manual verification.\n"
    flog(print_this, args_dict['logfile_name_w_abs_path'])

    print_this = "\nPress enter if this dataset looks ok.\n"
    if ("kimd999" in home_dir_path):
      nonBlockingRawInput(print_this)
    else:
      input(print_this)
    # James thinks that spot2pdb should be ran for merged dataset,
    # Sam observed as if spot2pdb is ran for each mrc file? rather than merged data?
    # However, as Doo Nam sees, spot2pdb should be ran in a folder that has SPOT.XDS and XPARM.XDS
    # This folder is per mrcs rather than merged data per same SPACE GROUP and similar UNIT CELL
  ######### <end> manual check of spot2pdb
  '''
  ############### <end> spot2pdb


  return_from_run_xscale_to_scale_after_xds = xscale.run_xscale_to_scale_after_xds(mrc_w_path, output_folder_name, args_dict)
  if return_from_run_xscale_to_scale_after_xds == False:
    return False
  
  SPACE_GROUP_NUMBER = retrieve_SPACE_GROUP_NUMBER(args_dict, "XSCALE.LP")
  flog(f"SPACE_GROUP_NUMBER for this dataset:{SPACE_GROUP_NUMBER}", args_dict['logfile_name_w_abs_path'])
  flog_wo_print(f"SPACE_GROUP_NUMBER for this dataset:{SPACE_GROUP_NUMBER}", args_dict['summary_logfile_name_w_abs_path'])

  UNIT_CELL_CONSTANTS = retrieve_UNIT_CELL_CONSTANTS(args_dict, "XSCALE.LP")
  flog(f"UNIT_CELL_CONSTANTS for this dataset:{UNIT_CELL_CONSTANTS}", args_dict['logfile_name_w_abs_path'])
  flog_wo_print(f"UNIT_CELL_CONSTANTS for this dataset:{UNIT_CELL_CONSTANTS}", args_dict['summary_logfile_name_w_abs_path'])

  return returned_from_run_xds # this is more_crystal_needed
#################### end of def per_each_mrc_file_both_single_and_multiple_sections(mrc_w_path)


# for both small molecule and protein
def phasing(args_dict):
  print_this = "phasing per each same SPACE GROUP and similar UNIT_CELL"
  flog(print_this, args_dict['logfile_name_w_abs_path'])
   
  result_of_xdsconv, output_file_name_from_xdsconv = xdsconv.xdsconv(args_dict)
  if (result_of_xdsconv == False):
    return False

  if (
     (str((args_dict['protein']).upper()) == "FALSE") 
     or (str((args_dict['protein']).upper()) == "F")
     ):
    print_this = "User's target is small molecule. Therefore, AutoMicroED will run xdsconv and shelx."
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    #return_from_shelx = shelx(args_dict, output_file_name_from_xdsconv)
    #TypeError: 'module' object is not callable

    return_from_shelx = shelx.shelx(args_dict, output_file_name_from_xdsconv)

    return return_from_shelx
  else:
    print_this = "User's target is protein. Therefore, AutoMicroED will run f2mtz, phaser-MR and phenix-refine."
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    return_from_f2mtz = protein.f2mtz(args_dict)
    if (return_from_f2mtz == False):
      return False
    return_from_phaser_mr = protein.phaser_mr(args_dict)
    if (return_from_phaser_mr == False):
      return False
    return_from_see_LLG_TFZ = protein.see_LLG_TFZ(args_dict)
    return return_from_see_LLG_TFZ
#################### end of def phasing(logfile_name_w_abs_path)


def receive_from_user(parameter):
  if (parameter == "d_not_calibrated"):
    print_this = "\nEnter 'd_not_calibrated'."
    print_this = print_this + "\n\tEMPIAR-10293    -> 4679"
    print_this = print_this + "\n\tketone tutorial -> 592.77 for 1053 calibrated distance"
    print_this = print_this + "\n\tOther example   -> 2640"
    print_this = print_this + "\nEnter now (Enter what cryo-EM equipment (like Krios) shows as is rather than calibrated distance.):"
  elif (parameter == "d_calibration_1st_coef"):
    print_this = "\nEnter 'd_calibration_1st_coef'."
    print_this = print_this + "\n\tketone tutorial -> 1.8"
    print_this = print_this + "\n\tsee (git repo)/templates/args_file/explanation_of_args.txt for more detail"
    print_this = print_this + "\nEnter 'd_calibration_1st_coef' now:"
  elif (parameter == "d_calibration_2nd_coef"):
    print_this = "\nEnter 'd_calibration_2nd_coef'."
    print_this = print_this + "\n\tketone tutorial -> -14"
    print_this = print_this + "\n\tsee (git repo)/templates/args_file/explanation_of_args.txt for more detail"
    print_this = print_this + "\nEnter 'd_calibration_2nd_coef' now:"
  elif (parameter == "Generate_LATT_SYMM_from_website"):
    print_this = "\nEnter 'Generate_LATT_SYMM_from_website'."
    print_this = print_this + "\nIf it is True, automatic generation of LATT and SYMM by phenix will not be performed."
    print_this = print_this + "\nEnter now (either True or False only):"
  elif (parameter == "least_completeness_overall"):
    print_this = "\nEnter least_completeness_overall"
    print_this = print_this + "\nAutoMicroED will use more crystal until it reaches this target."
    print_this = print_this  + "\nHigher target it recommended."
    print_this = print_this  + "\nFor ketone tutorial, 95 was enough."
    print_this = print_this + "\nEnter least_completeness_overall now:"
  elif (parameter == "ORGX"):
    print_this = "\nEnter ORGX"
    print_this = print_this + "\n\t(ketone tutorial's 2_20190913-162354.mrc -> 1940)"
    print_this = print_this + "\n\t(ketone tutorial's 3_20190913-163300.mrc -> 1921)"
    print_this = print_this + "\n\t(empiar-10293                            -> 2047)"
    print_this = print_this + "\nEnter ORGX now:"
  elif (parameter == "ORGY"):
    print_this = "\nEnter ORGY"
    print_this = print_this + "\n\t(ketone tutorial's 2_20190913-162354.mrc -> 2011)"
    print_this = print_this + "\n\t(ketone tutorial's 3_20190913-163300.mrc -> 2050)"
    print_this = print_this + "\n\t(empiar-10293                            -> 2020)"
    print_this = print_this + "\nEnter ORGY now:"
  elif (parameter == "voltage_of_the_microscope"):
    print_this = "\nEnter voltage of the microscope (kV) (either 200 or 300 only):"
  elif (parameter == "protein"):
    print_this = "\nSpecify whether this is for protein or small molecule"
    print_this = print_this + "\n\t(if this is protein, enter T, otherwise enter F)"
    print_this = print_this + "\nEnter protein now:"
  elif (parameter == "NX"):
    print_this = "\nEnter NX"
    print_this = print_this + "\n\t(ketone tutorial  -> 4096)"
    print_this = print_this + "\nEnter NX now:"
  elif (parameter == "NY"):
    print_this = "\nEnter NY"
    print_this = print_this + "\n\t(ketone tutorial  -> 4096)"
    print_this = print_this + "\nEnter NY now:"
  elif (parameter == "outdir"):
    print_this = "\nEnter outdir"
    print_this = print_this + "\n\t(Note) All spaces (if any) of user entered outdir name will be replaced to '_'"
    print_this = print_this + "\nEnter outdir now:"
  elif (parameter == "ROTATION_AXIS"):
    print_this = "\nEnter ROTATION_AXIS"
    print_this = print_this + "\n\t(ketone tutorial -> 1 0 0)"
    print_this = print_this + "\nEnter ROTATION_AXIS now:"
  elif (parameter == "SFAC"):
    print_this = "\nEnter SFAC"
    print_this = print_this + "\n\t(if ketone tutorial -> C H N O)"
    print_this = print_this + "\nEnter SFAC now:"

  elif (parameter == "spot2pdb_folder"):
    print_this = "\nEnter spot2pdb_folder"
    print_this = print_this + "\n\t(for example, /opt/apps/AutoMicroED)"
    print_this = print_this + "\nEnter spot2pdb_folder now and press enter:"
  
  elif (parameter == "spot2pdb_RESOLUTION_RANGE_max"):
    print_this = "spot2pdb_RESOLUTION_RANGE_max is not specified in user's args_file"
    print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt to see an example of spot2pdb_RESOLUTION_RANGE_max"
    print_this = print_this + "\n\t(For example) spot2pdb_RESOLUTION_RANGE 0.5 4"
    print_this = print_this + "\n\tFor now, enter spot2pdb_RESOLUTION_RANGE_max"
    print_this = print_this + "\n\t\t(For example, non-protein target -> 4)"
    print_this = print_this + "\n\t\t(For example,     protein target -> 999)"
    print_this = print_this + "\nEnter spot2pdb_RESOLUTION_RANGE_max now:"
  
  elif (parameter == "spot2pdb_RESOLUTION_RANGE_min"):
    print_this = "spot2pdb_RESOLUTION_RANGE_min is not specified in user's args_file"
    print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt for an example of spot2pdb_RESOLUTION_RANGE_min"
    print_this = print_this + "\n\tFor now, enter spot2pdb_RESOLUTION_RANGE_min"
    print_this = print_this + "\n\t(For example, non-protein target -> 0.5)"
    print_this = print_this + "\n\t(For example,     protein target -> 6)"
    print_this = print_this + "\nEnter spot2pdb_RESOLUTION_RANGE_min now:"

  elif (parameter == "TEST_RESOLUTION_RANGE_max"):
    print_this = "\nEnter TEST_RESOLUTION_RANGE_max"
    print_this = print_this + "\n\t(For ketone tutorial -> 10)"
    print_this = print_this + "\nEnter TEST_RESOLUTION_RANGE_max now:"
  
  elif (parameter == "TEST_RESOLUTION_RANGE_min"):
    print_this = "\nEnter TEST_RESOLUTION_RANGE_min"
    print_this = print_this + "\n\t(For ketone tutorial -> 0.5)"
    print_this = print_this + "\nEnter TEST_RESOLUTION_RANGE_min now:"
  
  elif (parameter == "UNIT"):
    print_this = "\nEnter UNIT"
    print_this = print_this + "\n\t(if ketone tutorial -> 20 0 0 0)"
    print_this = print_this + "\nEnter UNIT now:"
  elif (parameter == "UNIT_CELL_CONSTANTS"):
    print_this = "\nEnter UNIT_CELL_CONSTANTS"
    print_this = print_this + "\n\t(For example -> 68.15   169.75   193.81  90.000  90.058  90.000)"
    print_this = print_this + "\nEnter UNIT_CELL_CONSTANTS now:"
  else:
    print_this = "\nEnter " + str(parameter) + ":"  
  
  parameter_from_user = input(print_this)
  
  if (parameter == "outdir"):
    parameter_from_user = parameter_from_user.replace(" ", "_")

  print ("\n" + str(parameter) + ": " + str(parameter_from_user))
  return parameter_from_user
########## end of def receive_from_user(parameter)


def retrieve_SPACE_GROUP_NUMBER(args_dict, XSCALE_LP_with_path):
  # flog(f"cwd:{os.getcwd()}", args_dict['logfile_name_w_abs_path'])
  # flog_wo_print(f"cwd:{os.getcwd()}", args_dict['summary_logfile_name_w_abs_path'])
  if (os.path.isfile(XSCALE_LP_with_path) == True):
    f_in  = codecs.open(XSCALE_LP_with_path, 'r')
  else:
    print_this = str(XSCALE_LP_with_path) + " doesn't exist.\n"
    print_this = print_this + "\t(note) Space group is available in XSCALE.LP that a user generates for each individual crystal."
    print_this = print_this + "\tXDSCONV.LP is the file you generate when you are ready to move to shelxt after merging several."
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
    return False
  for line in f_in:
    if (line[:20] == " SPACE_GROUP_NUMBER="):
      splited_line = line.split()
      SPACE_GROUP_NUMBER = splited_line[1]
      break
  return SPACE_GROUP_NUMBER
########## end of def retrieve_SPACE_GROUP_NUMBER()


def retrieve_UNIT_CELL_CONSTANTS(args_dict, source_file):
  print_this = "\t(note) Doo Nam saw that UNIT_CELL_CONSTANTS from XSCALE.LP is identical as those from XDSCONV.LP\n"
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  f_in  = codecs.open(source_file, 'r')
  for line in f_in:
    if (line[:21] == " UNIT_CELL_CONSTANTS="):
      UNIT_CELL_CONSTANTS = line[22:]
      UNIT_CELL_CONSTANTS = UNIT_CELL_CONSTANTS.lstrip()
      f_in.close()
      break
  return UNIT_CELL_CONSTANTS
########## end of def retrieve_UNIT_CELL_CONSTANTS(source_file)


def show_header(title):
    multiply_asterisk = 60
    print ("\n" + '#'*multiply_asterisk)
    number_of_remaining_sharp = multiply_asterisk -len(title) 
    put_this_number_of_sharp = int(int(number_of_remaining_sharp)/2)
    print ('#'*(put_this_number_of_sharp-2) + title + " " + '#'*(put_this_number_of_sharp-2))
    print ('#'*multiply_asterisk + "\n")
########### end of show_header function

    
def show_time(process, time_start, time_end):
    time_took = "\n" + str(process) + " finished in "
    if (round((time_end-time_start)/60, 1) < 1):
      time_took = time_took + str(round((time_end-time_start), 1)) + " seconds "
    elif (round((time_end-time_start)/60/60, 1) < 1):
      time_took = time_took + str(round((time_end-time_start)/60, 1)) + " minutes "
    else:
      time_took = time_took + str(round((time_end-time_start)/60/60, 1)) + " hours "
    time_took = time_took + "(wall clock).\n\n"
    return time_took
########## end of show_time function
            

def waiting(wait_seconds):
  print_this = "Waiting for additional " + str(wait_seconds) + " seconds.\n"
  print (print_this)
  time.sleep(wait_seconds)
############ end of def waiting(wait_seconds)


answer = None
def wait_10_seconds(n=10):
  time.sleep(n)
  if answer != None:
      return
  print_this = str(n) +  " seconds passed without user's input. AutoMicroED will just continue."
  print (print_this)
