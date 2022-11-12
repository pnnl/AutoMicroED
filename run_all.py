#!/usr/bin/env python

import argparse, codecs, glob, os, platform, shutil, subprocess, sys, time
from datetime import datetime
from threading import Thread

if (__name__ == "__main__") :
  args = sys.argv[0:]
  
  explain_user_input = '''
  Method 1 (basic, recommended for interactive running)
  Usage: python run_all.py <image input list>
  Example: python /Users/kimd999/Dropbox/script/python/cryoEM/AutoMicroED/run_all.py mrc_file.list
  
  Method 2 (advanced, recommended for continuous running)
  Usage: python run_all.py <image input list> <args>
  Example: python /Users/kimd999/Dropbox/script/python/cryoEM/AutoMicroED/run_all.py mrc_file.list args_file.txt
    
  Note
  Exemplar mrc_file.list would have \n\t/Users/kimd999/research/microED/2_20190913_162354.mrc\n\t/Users/kimd999/research/microED/3_20190913_163300.mrc
  This mrc_fie.list can be generated by for example, kimd999$ ls $PWD/*.mrc > mrc_file.list
  AutoMicroED will use all mrc files in mrc_file.list until it reaches user specified completeness.
    
  If a user provided <args list> file as well, then arguments in there will be used automatically rather than waiting for user to enter input values interactively.
  
  Exemplar input files are in AutoMicroED/templates/input_files'''
  if (len(args) < 2):
    print (explain_user_input)
    exit(1)
   
  ''' 
  # this version check doesn't work if later sentences do not conform to python3
  if (str(sys.version[:1]) == "2"):
    print ("AutoMicroED is optimized with python3 rather than python2.\n\nTherefore, run")
    print ("\talias python='python3'")
    print ("and run AutoMicroED again")
    print ("\n\nAlternatively a user can do")
    print ("\tpython3 <git repo>/run_all.py <mrc.list> <args.list>")
    print ("\n\tIf a user wants to use alias, then put -> alias MicroED=\"/home/kimd999/bin/miniconda3/bin/python3.8 /gpustorage/automation/MicroED/Scripts/AutoMicroED/run_all.py\"")
    print ("\tinto ~/.bashrc (of course, modify PATH to user's own one)")
    exit(1) 

    # "If a user uses pnnl_kriosgpu, \
    #       alias MicroED=\"/home/kimd999/bin/miniconda3/bin/python3.8 /gpustorage/automation/MicroED/Scripts/AutoMicroED/run_all.py\" works
  '''

  if not hasattr(sys, "version_info") or sys.version_info < (3,7):
    raise ValueError("Script requires Python 3.7 or higher!")


  today = datetime.now()
  time_now = today.strftime('%Y/%m/%d') + "/" + str(today.hour) + ":" + str(today.minute) + ":" + str(today.second)
  
  py_file = args[0]
  list_of_mrc_file_or_smv_folder = args[1]
  list_of_mrc_file_or_smv_folder_w_abs_path = os.path.abspath(list_of_mrc_file_or_smv_folder)
  
  repo_location = os.path.dirname(os.path.abspath(py_file))
  
  util_path = repo_location + "/util/"
  sys.path.insert(0, util_path)
  from util import *
  
  args_dict = {} # this should live before args_file_parse
  starting_dir = os.getcwd()
  args_dict['starting_dir'] = starting_dir
  args_dict['repo_location'] = repo_location


  if (len(args) >= 3):
    args_file = args[2]
    args_file_w_abs_path = os.path.abspath(args_file)  
    args_dict['args_file_w_abs_path'] = os.path.abspath(args_file_w_abs_path)

  #print (f"args_dict:{args_dict}")

  if (os.path.isdir("output") == False):
    os.mkdir("output")
  os.chdir("output")  

  working_folder = today.strftime('%Y%m%d') + "_" + str(today.hour) + "_" + str(today.minute) + "_" + str(today.second)
  
  working_folder_abs_path = os.path.abspath(working_folder)
  
  os.mkdir(working_folder_abs_path)
  os.chdir(working_folder_abs_path)
  
  logfile_name = "full.log"
  args_dict['logfile_name_w_abs_path'] = os.path.abspath(logfile_name)
  
  if (os.path.isfile(args_dict['logfile_name_w_abs_path']) == True):
    os.remove(args_dict['logfile_name_w_abs_path'])
  
  args_dict['summary_logfile_name_w_abs_path'] = args_dict['logfile_name_w_abs_path'][:-8] + "summary.log"


  ############### <begin> read args file and populate args_dict
  if (len(args) >= 3):
    args_dict_renewed = args_file_parse(args_dict)
    if (args_dict_renewed == False):
      print_this = "\nargs_file needs to be updated properly. Please refer (user's AutoMicroED git repo)/templates/args_file/explanation_of_args.txt for more detail."
      print_this = print_this + "\nAutoMicroED will exit now."
      flog(print_this, args_dict['logfile_name_w_abs_path'])
      flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
      exit(1)
    else:
      args_dict = args_dict_renewed
    print_this = "args_dict after population:" + str(args_dict)
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
    
  ############### <end> read args file and populate args_dict


  print_this = "working_folder_abs_path:" + str(working_folder_abs_path)
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])

  print_this = "User entered arguments:" + str(args)
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])


  ############### <begin> Check existence of elements in input mrc_file_or_smv_folder
  mrc_file_or_smv_folder_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
  for mrc_file in mrc_file_or_smv_folder_opened:
    if (mrc_file == "\n") or (mrc_file == ""):
      continue
    
    mrc_w_path = mrc_file.rstrip()
    
    if (os.path.exists(mrc_w_path) == False):
      print_this = str(mrc_w_path) + " doesn't exist. Please fix file name/path.\n"
      flog(print_this, args_dict['logfile_name_w_abs_path'])
      exit(1)
  mrc_file_or_smv_folder_opened.close()
  ############### <end> Check existence of elements in input mrc_file_or_smv_folder


  ############### <begin> Identify whether input mrc_file_or_smv_folder is for mrc/smv
  mrc_file_or_smv_folder_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
  input_list_has_mrc = False
  for mrc_file in mrc_file_or_smv_folder_opened:
    if (".mrc" in mrc_file):
      input_list_has_mrc = True
      break
  mrc_file_or_smv_folder_opened.close()
  args_dict['input_list_has_mrc'] = input_list_has_mrc
  ############### <end> Identify whether input mrc_file_or_smv_folder is for mrc/smv
  

  ############### <begin> count columns, NX, NY, sections of the FIRST input mrc  
  if (args_dict['input_list_has_mrc'] == True):
    mrc_file_list_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
    for mrc_file in mrc_file_list_opened:
      if ".mrc" in mrc_file:
        mrc_w_path = mrc_file.rstrip()
        columns, sections = count_columns_sections_in_each_mrc_file_by_mrcfile(args_dict, mrc_w_path)
        if (columns == None) or (columns == False):
          print_this = "columns of mrc is either None or False. Is this mrc input file correct?"
          flog(print_this, args_dict['logfile_name_w_abs_path'])
          flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
          exit(1)
        args_dict['columns'] = columns
        args_dict['NX'] = args_dict['columns']
        args_dict['NY'] = args_dict['columns']
        args_dict['sections'] = sections
        break
      else: # user provided .mrcs file
        break
    mrc_file_list_opened.close()

  else: # if (args_dict['input_list_has_mrc'] = False # so user's file is smv/img
    pass
    #args_dict['sections'] = 1
    # Doo Nam and Sam believe that smv/img file are for single image never stacks as mrcs

    '''
    # <begin> check whether a user specified ORGX, ORGY
    if ("ORGX" not in args_dict) or ("ORGY" not in args_dict):
      ORGX_specified = False
      for key, value in args_dict.items():
        ##print (fkey:{key}")
        ##print (flen(key):{len(key)}")
        if (len(key) == 2):
          if ("ORGX" in key[0]):
            ORGX_specified = True
            break
      if (ORGX_specified == False):
        print_this = "ORGX and ORGY should be specified manually when a user provides smv only (not mrc)."
        flog(print_this, args_dict['logfile_name_w_abs_path'])
        flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
        exit(1)
    # <end> check whether a user specified ORGX, ORGY
    '''
  ############### <end> count columns, NX, NY, sections of the FIRST input mrc



  ############### <begin> check xds_par, xscale, xdsconv path
  try:
    path = subprocess.check_output(["which", "xds_par"]).decode('UTF-8')
    print_this = "xds_par is located by PATH. The path of xds_par:" + str(path)
    flog(print_this, args_dict['logfile_name_w_abs_path'])
  except:
    print_this ="AutoMicroED can't find xds_par in user's PATH."
    print_this = print_this + "\nPlease add xds_par folder to PATH and run AutoMicroED again because same PATH has forkxds as well."
    # devel comment: because of forkxds, do not use xds_folder argument, mandate users to set PATH
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    write_this = '''For example,
    emacs ~/.bash_profile
 
    (copy and paste this to any line)
    export PATH="/gpustorage/DN/XDS-INTEL64_Linux_x86_64":$PATH    
    
    (save, for mac keyboard Ctrl-x-s)
 
    (exit emacs, for mac keyboard Ctrl-x-c)
 
    source ~/.bash_profile (or opening a new tab to take effect of new change in ~/.bash_profile'''

    #export PATH="/gpustorage/DN/XDS-INTEL64_Linux_x86_64":$PATH    # for PNNL_Krios_GPU.
    #export PATH="/home/kimd999/bin/XDS-INTEL64_Linux_x86_64":$PATH # for PNNL_HPC_Cascade.

    flog(write_this, args_dict['logfile_name_w_abs_path'])
    exit(1)
  ################ <end> check xds_par, xscale, xdsconv path
  
  
  
  ################ <begin> check cad, f2mtz, shelxt, shelxl path
  try:
    subprocess.check_output(["which", "shelxt"])
  except:
    if ('ccp4_folder' not in args_dict.keys()):
      print_this ="AutoMicroED can't find shelxt in user's PATH."
      flog(print_this, args_dict['logfile_name_w_abs_path'])
      
      print_this ="Solution #1. Add shelxt folder to ~/.bashrc PATH and run AutoMicroED again. \n"
      print_this = print_this + '''For example,
      emacs ~/.bash_profile
   
      (copy and paste this to any line)
      export PATH="/home/kimd999/bin/ccp4/ccp4-7.1/bin":$PATH  
      
      (save by Ctrl-x-s for mac keyboard)
      (exit emacs by Ctrl-x-c for mac keyboard)
   
      source ~/.bash_profile (or opening a new tab to take effect of new change in ~/.bash_profile'''

      #export PATH="/home/kimd999/bin/ccp4/ccp4-7.1/bin":$PATH    # for PNNL_Krios_GPU.
      #export PATH="/msc/krios/bin":$PATH                         # for PNNL_HPC_cascade.
      flog(print_this, args_dict['logfile_name_w_abs_path'])
      
      
      print_this ="Solution #2. Add ccp4_folder (that has cad, f2mtz, shelxt, shelxl) to user's args_file and run AutoMicroED again. \n"
      print_this = print_this + '''For example,
      emacs args_file.txt
      
      (copy and paste this to any line)
      ccp4_folder /home/kimd999/bin/ccp4/ccp4-7.1/bin
      
      (save by Ctrl-x-s for mac keyboard)
      (exit emacs by Ctrl-x-c for mac keyboard)
      '''
      flog(print_this, args_dict['logfile_name_w_abs_path'])
      
      exit(1)
  ################ <end> check cad, f2mtz, shelxt, shelxl path
  
  process = " Automatic MicroED"
  show_header(process)
  start_time = time.time()
  
  path_before_opening_list_of_mrc_file_or_smv_folder = os.getcwd()

  if (args_dict['input_list_has_mrc'] == True):
    if (
       ('Bypass_movie_inspection' not in args_dict.keys()) 
       or (args_dict['Bypass_movie_inspection'].upper() == "F")
       or (args_dict['Bypass_movie_inspection'].upper() == "FALSE")
       ):
      check_movie_quality()

    ############### <begin> args_dict['sections']) > 1 (e.g. mrcs input)
    if (int(args_dict['sections']) > 1): 

      mrc_file_list_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
      mrc_file_number = 0
      for mrc_file in mrc_file_list_opened:
        mrc_w_path = mrc_file.rstrip()
        #write_this = "mrc_file:" + str(mrc_file)
        #flog_wo_print(write_this, args_dict['logfile_name_w_abs_path'])
        
        if (mrc_file == "\n") or (mrc_file == ""):
          continue
        
        mrc_file_number = mrc_file_number + 1
        if (platform.system() == "Linux"):
          
          mrc_file_basename = os.path.basename(mrc_file)
          intermediate_output_folder_name = os.path.splitext(mrc_file_basename)[0]
          
          os.mkdir(intermediate_output_folder_name)
          os.chdir(intermediate_output_folder_name)
          os.mkdir("xds")
          os.mkdir("img")
          os.chdir("img")
    
          per_each_mrc_smv_file_both_single_and_multiple_sections(args_dict, 
                                                        mrc_w_path, 
                                                        intermediate_output_folder_name)

          more_crystal_needed = xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections(args_dict, 
                                                                    mrc_w_path, 
                                                                    intermediate_output_folder_name)
          
          if (more_crystal_needed == "failed"):
            exit(1)
          elif (more_crystal_needed == "CORRECT.LP not found"):
            write_this = "[xds] CORRECT.LP not found even after many troubleshootings."
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
          else:
            write_this = "more_crystal_needed: " + str(more_crystal_needed)
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            
            if (more_crystal_needed == True):
              write_this = "AutoMicroED will feed more mrcs file (if any)."
              flog(write_this, args_dict['logfile_name_w_abs_path'])
          
          os.chdir(path_before_opening_list_of_mrc_file_or_smv_folder)
          
          if (more_crystal_needed == False):
            break
          
        else: # macOS
          mrc_file_basename = os.path.basename(mrc_file)
          write_this = "mrc_file_basename:" + str(mrc_file_basename)
          flog(write_this, args_dict['logfile_name_w_abs_path'])
          
          intermediate_output_folder_name = os.path.splitext(mrc_file_basename)[0]
          
          os.mkdir(intermediate_output_folder_name)
          os.chdir(intermediate_output_folder_name)
          
          os.mkdir("xds")
          
          os.mkdir("img")
          os.chdir("img")
          
          per_each_mrc_smv_file_both_single_and_multiple_sections(args_dict, 
                                                          mrc_w_path, 
                                                          intermediate_output_folder_name)

          more_crystal_needed = xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections(args_dict, 
                                                                  mrc_w_path, 
                                                                  intermediate_output_folder_name)
          write_this = "more_crystal_needed: " + str(more_crystal_needed)
          flog(write_this, args_dict['logfile_name_w_abs_path'])
            
          if (more_crystal_needed == -999):
            exit(1)
            
          os.chdir(path_before_opening_list_of_mrc_file_or_smv_folder)
          if (more_crystal_needed == False):
            break
      mrc_file_list_opened.close()
      ######### end of for mrc_file in mrc_file_or_smv_folder_opened
          
      if (mrc_file_number == 0):
        write_this = "mrc_file_number = 0. Please populate mrc_list first."
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        exit(1)
    
      if (more_crystal_needed != "no CORRECT.LP found"):
        write_this = "more_crystal_needed after looping through list_of_mrc_file_or_smv_folder: " + str(more_crystal_needed)
        args_dict['more_crystal_needed'] = more_crystal_needed
        flog(write_this, args_dict['logfile_name_w_abs_path'])
      else:
        print_this = "xds needs to be re-ran with other approach/data. Please analyze xds_XXX.log files.\n"
        print_this = print_this + "For example, xds binary might have been expired like \"Sorry, license expired on 31-Mar-2022\""
        
        print (print_this)
        exit(1)
    ############### <end>   args_dict['sections']) > 1 (e.g. mrcs input)


    ############### <begin> single frame mrc (e.g. individual mrc)
    else: # (args_dict['sections']) == 1)
      mrc_file_number = 0
      mrc_file_or_smv_folder_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
      
      more_crystal_needed = None
      for mrc_file in mrc_file_or_smv_folder_opened:
        mrc_w_path = mrc_file.rstrip()
        
        if (mrc_file == "\n") or (mrc_file == ""):
          continue
        
        if (mrc_w_path.find('.mrc') == -1):
            print_this = str(mrc_w_path) + " doesn't have .mrc.\nPerhaps, a user entered args_file rather than mrc.list?\n"
            print_this = print_this + " AutoMicroED exits now.\n"
            print (print_this)
            end_time = time.time()
    
            write_this = show_time(process, start_time, end_time)
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
            exit(1)
    
        if (os.path.isfile(mrc_w_path) == False):
          print_this = str(mrc_w_path) + " doesn't exist. AutoMicroED exits now.\n"
          print (print_this)
          end_time = time.time()
    
          write_this = show_time(process, start_time, end_time)
          flog(write_this, args_dict['logfile_name_w_abs_path'])
          flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
          exit(1)
        
        mrc_file_number = mrc_file_number + 1
        
        base_mrc_name = os.path.basename(mrc_w_path)
        splited_base_mrc_name = base_mrc_name.split(".mrc")
        splited_base_mrc_name2 = splited_base_mrc_name[0].split("_")
        image_num = int(splited_base_mrc_name2[len(splited_base_mrc_name2)-1])
        
        if (image_num <= 3): # Irina doesn't like to use first 3 images
           continue
          
        mrc_file_basename = os.path.basename(mrc_w_path)
        intermediate_output_folder_name = mrc_file_basename[:-9]
        
        # (Note) because of this, single frame mrc_file can be processed similarly as multi frame mrc_file
        if (os.path.isdir(intermediate_output_folder_name) == False):
          os.mkdir(intermediate_output_folder_name)
          os.chdir(intermediate_output_folder_name)
          print (os.getcwd())
          
          if (os.path.isdir("xds") == False):
            os.mkdir("xds")
          
          if (os.path.isdir("img") == False):
            os.mkdir("img")
          os.chdir("img")
          
          
          print_this = "(single column) mrc file that is used for xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections:" + str(mrc_w_path)
          flog(print_this, args_dict['logfile_name_w_abs_path'])
          
          per_each_mrc_smv_file_both_single_and_multiple_sections(args_dict, 
                                                          mrc_w_path, 
                                                          intermediate_output_folder_name)

          more_crystal_needed = xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections(args_dict, 
                                                          mrc_w_path, 
                                                          intermediate_output_folder_name)

          if (more_crystal_needed == "no CORRECT.LP found"):
              flog("no CORRECT.LP found", args_dict['logfile_name_w_abs_path'])
          elif (more_crystal_needed == "Running xds failed."):
              flog("Running xds failed. Please analyze xds.log files.", args_dict['logfile_name_w_abs_path'])
              exit(1)
          else:
            write_this = "more_crystal_needed: " + str(more_crystal_needed)
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            
            if (more_crystal_needed == True):
              write_this = "AutoMicroED will feed more individual mrc (column=1) file (if there are any)."
              flog(write_this, args_dict['logfile_name_w_abs_path'])

          if (more_crystal_needed == -999):
            exit(1)
            
          os.chdir(path_before_opening_list_of_mrc_file_or_smv_folder)
          if (more_crystal_needed == False):
            break
          
      mrc_file_or_smv_folder_opened.close()
      
      if (mrc_file_number == 0):
        write_this = "mrc_file_number = 0. Please populate mrc_list first."
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        exit(1)
   
      if more_crystal_needed == None:
        print ("more_crystal_needed is not defined. Maybe xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections never ran since # of each mrc < 4")
        exit(1)

      args_dict['more_crystal_needed'] = more_crystal_needed
      if (more_crystal_needed != "no CORRECT.LP found"):
        write_this = "more_crystal_needed after looping through list_of_mrc_file_or_smv_folder: " + str(more_crystal_needed)
        flog(write_this, args_dict['logfile_name_w_abs_path'])
      else:
        print_this = "xds needs to be re-ran with other approach/data."
        print (print_this)
        exit(1)
    ############### <end>   single frame mrc (e.g. individual mrc)
    

  else: # input_list_has_mrc == False (such as smv/img file)
    smv_folder_opened = codecs.open(list_of_mrc_file_or_smv_folder_w_abs_path, 'r')
    for each_smv_folder in smv_folder_opened:
      each_smv_folder = each_smv_folder.rstrip()

      write_this = "each_smv_folder:" + str(each_smv_folder)
      flog(write_this, args_dict['logfile_name_w_abs_path'])
      #/gpustorage/MicroEDProc/SMP/CycA_SBGrid/752/20181220-112002/img/

      if (each_smv_folder == "\n") or (each_smv_folder == ""):
        continue

      for each_img_file in os.listdir(each_smv_folder):
        if each_img_file.endswith(".img") or each_img_file.endswith(".smv"):
          prefix_of_img_file = each_img_file[:len(each_img_file)-9]
          args_dict['prefix_of_img_file'] = prefix_of_img_file
          break

      if (each_smv_folder[len(each_smv_folder)-1]) == "/":
        each_smv_folder = each_smv_folder[:len(each_smv_folder)-1]

      intermediate_output_folder_name = each_smv_folder.split('/')[-2]
      #print (fintermediate_output_folder_name:{intermediate_output_folder_name}")
      # smv only -> 165749merged
      
      os.mkdir(intermediate_output_folder_name)
      os.chdir(intermediate_output_folder_name)
      
      os.mkdir("xds")
      os.mkdir("img")
      os.chdir("img")

      command = "cp " + str(each_smv_folder).rstrip() + "/*.img ."
      print(command)
      os.system(command)

      per_each_mrc_smv_file_both_single_and_multiple_sections(args_dict, 
                                                          mrc_w_path, 
                                                          intermediate_output_folder_name)

      more_crystal_needed = xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections(args_dict, 
                                                                mrc_w_path, 
                                                                intermediate_output_folder_name)
      if (more_crystal_needed == "failed"):
        exit(1)
      elif (more_crystal_needed == "CORRECT.LP not found"):
        write_this = "[xds] CORRECT.LP not found even after many troubleshootings."
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
        exit(1)
      elif (more_crystal_needed == "Running xds failed."):
        flog("Running xds failed. Please analyze xds.log files.", args_dict['logfile_name_w_abs_path'])
        exit(1)
      else:
        write_this = "more_crystal_needed: " + str(more_crystal_needed)
        flog(write_this, args_dict['logfile_name_w_abs_path'])
        
        if (more_crystal_needed == True):
          write_this = "AutoMicroED will feed more smv/img file (if there are any)."
          flog(write_this, args_dict['logfile_name_w_abs_path'])
      
      os.chdir(path_before_opening_list_of_mrc_file_or_smv_folder)
      
      if (more_crystal_needed == False):
        break

    smv_folder_opened.close()
    #### end of for each_smv_folder in smv_folder_opened:

    if (more_crystal_needed != "no CORRECT.LP found"):
      write_this = "bool(more_crystal_needed) after looping through list_of_mrc_file_or_smv_folder: " + str(more_crystal_needed)
      args_dict['more_crystal_needed'] = more_crystal_needed
      flog(write_this, args_dict['logfile_name_w_abs_path'])
    else:
      print_this = "xds needs to be re-ran with other approach/data."
      print (print_this)
      exit(1)
  ####end of else: # input_list_has_mrc == False (such as smv and img file)



  ###### <begin> Common for stack and single frame mrc 
  # (after xds_retrieve_UNIT_CELL_per_each_mrc_file_both_single_and_multiple_sections)

  returned_from_generate_each_SPACE_GROUP_folder = generate_each_SPACE_GROUP_folder(args_dict)
  if (returned_from_generate_each_SPACE_GROUP_folder == False):
    end_time = time.time()
  
    write_this = show_time(process, start_time, end_time)
    flog(write_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])




    if ("outdir" not in args_dict):
      print_this = "\noutdir is not defined in args_file\n"
      print_this = print_this + "Either specify it args_file (for later AutoMicroED run)\n"
      print_this = print_this + "or enter here (for example full_range_xds)."
      print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt for an example of outdir"
      print (print_this)


      #Thread(target = wait_10_seconds).start()
      answer = receive_from_user("outdir")    
      if answer != None:
        args_dict['outdir'] = answer
        working_folder = args_dict['outdir'] + "_" + working_folder

    else:
      working_folder = args_dict['outdir'] + "_" + working_folder

    # common regardless whether user specified outdir or not
    os.chdir("..")
    new_working_folder_abs_path = os.path.abspath(working_folder)

    command = "mv " + str(working_folder_abs_path) + " " + str(new_working_folder_abs_path)
    os.system(command)




    exit(1)
    
  dir_before_entering_each_SPACE_GROUP = os.getcwd()
  for SPACE_GROUP_folder in glob.glob("SPACE_GROUP_*"):
    print_this = "SPACE_GROUP_folder:" + str(SPACE_GROUP_folder)
    flog(print_this, args_dict['logfile_name_w_abs_path'])
    flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])

    os.chdir(SPACE_GROUP_folder)
    
    generate_each_similar_UNIT_CELL_folder(args_dict)
    
    dir_per_SPACE_GROUP = os.getcwd()
    print ("directory per_SPACE_GROUP:" + str(dir_per_SPACE_GROUP))
    
    for entry in os.scandir('.'):
      if not entry.name.startswith('.') and entry.is_dir():
          cwd = os.getcwd()
          print ("cwd:" + str(cwd))
          os.chdir(entry.name)
    
          return_from_run_xscale_to_merge = xscale.run_xscale_to_merge(args_dict) 
          # just "merge" even if current_completeness <= target
          if (return_from_run_xscale_to_merge == False):
            exit(1)
            
          result_of_phasing = phasing(args_dict) # phasing seems to be needed to be ran per each UNIT_CELL folder
          if (result_of_phasing == False):
            write_this = "\t\tPhasing was not successful.\n"
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])

            end_time = time.time()
  
            write_this = show_time(process, start_time, end_time)
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])

            exit(1)
          else:
            write_this = "\t\tPhasing was successful.\n"
            flog(write_this, args_dict['logfile_name_w_abs_path'])
            flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])

          
          if ((str(args_dict['protein']).upper() == "TRUE") \
           or (str(args_dict['protein']).upper() == "T")):
            return_from_phenix_refine_fn = protein.phenix_refine_fn(args_dict)
          
          os.chdir(dir_per_SPACE_GROUP)
            
    os.chdir(dir_before_entering_each_SPACE_GROUP)

  
  closing_remark(args_dict)
  end_time = time.time()
  
  write_this = show_time(process, start_time, end_time)
  flog(write_this, args_dict['logfile_name_w_abs_path'])
  flog_wo_print(write_this, args_dict['summary_logfile_name_w_abs_path'])
  ###### <end> Common for stack and single frame mrc
  

  ###### <begin> final organization
  os.chdir(working_folder_abs_path)
  
  os.mkdir("archive")
  

  command = "cp " + str(args_dict['args_file_w_abs_path']) + " archive/user_specified_args_file.txt"
  os.system(command)

  command = "cp " + str(list_of_mrc_file_or_smv_folder_w_abs_path) + " archive/user_entered_mrc_list.txt"
  os.system(command)

  all_folders = os.listdir()
  for folder in all_folders:
    if "archive" in folder:
      pass
    elif "SPACE_" in folder:
      pass
    elif "summary.log" in folder:
      pass
    else:
      command = "mv " + str(folder) + " archive"
      os.system(command)
  
  command = "mv archive/user_* ."
  os.system(command)
  ###### <end> final organization


  if ("outdir" not in args_dict):
    print_this = "\noutdir is not defined in args_file\n"
    print_this = print_this + "Either specify it args_file (for later AutoMicroED run)\n"
    print_this = print_this + "or enter here (for example full_range_xds)."
    print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt for an example of outdir"
    print (print_this)


    #Thread(target = wait_10_seconds).start()
    answer = receive_from_user("outdir")    
    if answer != None:
      args_dict['outdir'] = answer
      working_folder = args_dict['outdir'] + "_" + working_folder

  else:
    working_folder = args_dict['outdir'] + "_" + working_folder

  # common regardless whether user specified outdir or not
  os.chdir("..")
  new_working_folder_abs_path = os.path.abspath(working_folder)

  command = "mv " + str(working_folder_abs_path) + " " + str(new_working_folder_abs_path)
  os.system(command)
