import argparse, codecs, glob, os, platform, random, shutil, signal, subprocess, sys, time
import protein, xds, xscale
import util

def enter_SYMM_automatically(f_out):
  f_in  = codecs.open("LATT_SYMM.txt", 'r')
  LATT_retrieved = False
  for line in f_in:
    if (LATT_retrieved == False):
      LATT_retrieved = True
    else:
      write_this = "SYMM " + str(line) + "\n"
      f_out.write(write_this) 
  f_in.close()
########## end of def enter_SYMM_automatically()


def enter_SYMM_from_website(home_dir_path, f_out):
  for i in range (3):
    SYMM_index = i + 1
    SYMM_name = "sym_record_" + str(SYMM_index)
    SYMM = ''
    print_this = "\nEnter SYMM (" + str(SYMM_index) + " out of 3):"
    
    if ("kimd999" in home_dir_path):
      print_this = "\nEnter " + str(SYMM_name) + " (for example, X,-Y,-Z):"
      SYMM = nonBlockingRawInput(print_this)
    else:      
      SYMM = input(print_this)

    if (SYMM == ""):
      print ("\tUser didn't enter SYMM.")
      print ("\tTherefore, AutoMicroED assigns automatically")
      if (SYMM_index == 1):
        SYMM = "X,-Y,-Z"
      elif (SYMM_index == 2):
        SYMM = "-X,Y,-Z"
      else:
        SYMM = "-X,-Y,Z"
      print ("SYMM:" + str(SYMM))
      
    write_this = "SYMM " + str(SYMM) + "\n"
    f_out.write(write_this)
########## end of def enter_SYMM_from_website()


def receive_from_user(parameter):
  print_this = "\nEnter " + str(parameter) + ":"  
  
  parameter_from_user = input(print_this)
  
  if (parameter == "outdir"):
    parameter_from_user = parameter_from_user.replace(" ", "_")

  print ("\n" + str(parameter) + ": " + str(parameter_from_user))
  return parameter_from_user
########## end of def receive_from_user(parameter)


def retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER):
  print ("\nGenerate LATT and SYMM records from https://cci.lbl.gov/cctbx/shelx.html")
  print_this = "\nFrom XSCALE.LP, SPACE_GROUP_NUMBER is retrived as " + str(SPACE_GROUP_NUMBER)
  print (print_this)
  LATT = receive_from_user("LATT")
  return LATT
########## end of def retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER)


def retrieve_LATT_SYMM_automatically(SPACE_GROUP_NUMBER, args_dict):
  print_this = "\nPHENIX will generate LATT and SYMM records automatically"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  write_this = "Current user's SPACE_GROUP_NUMBER=" + str(SPACE_GROUP_NUMBER) 
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])

  util_path = args_dict['repo_location'] + "/util/"
  run_this = os.path.join(util_path, "generate_LATT_SYMM.py")
  
  try:
    path = subprocess.check_output(["which", "phenix.python"]).decode('UTF-8')
    print(f"PATH of phenix.python is {path}")
    command = "phenix.python " + str(run_this) + " " + str(SPACE_GROUP_NUMBER)
  except:
    command = "/home/scicons/cascade/apps/phenix-dev-3900/build/bin/phenix.python " + str(run_this) + " " \
          + str(SPACE_GROUP_NUMBER)

  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  
  LATT = ''
  SYMM = ''
  f_in  = codecs.open("LATT_SYMM.txt", 'r')
  LATT_retrieved = False
  for line in f_in:
    if (LATT_retrieved == False):
      LATT = line
      LATT_retrieved = True
    else:
      SYMM = SYMM + str(line)
  f_in.close()
  
  return LATT
########## end of def retrieve_LATT_SYMM_automatically(SPACE_GROUP_NUMBER, args_dict)
