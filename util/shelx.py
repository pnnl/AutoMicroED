from datetime import datetime as dt
import codecs, os, platform, shutil, subprocess, sys, time
import util
import LATT_SYMM


def run_shelxl_no_cif(args_dict):
  process = "shelxl (refine the crystal structure)\n"
  start_time = time.time()
  util.show_header(process)
  
  starting_folder_for_shelxl = os.getcwd()
  
  os.mkdir("shelxl_no_cif")
  os.chdir("shelxl_no_cif")
  
  shutil.copyfile("../shelxt_input_from_xdsconv_a.res", "sol1.ins")
  shutil.copyfile("../shelxt_input_from_xdsconv_a.hkl", "sol1.hkl")
  
  print_this = "\t(note) \"shelxl is a very general crystal structure refinement program that is equally suitable for the refinement of minerals, organometallic structures, oligonucleotides, or proteins (or any mixture thereof) against X-ray or neutron single (or twinned!) crystal data.\"\n"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  try:
    subprocess.check_output(["which", "shelxl"])
    command = "shelxl sol1 > shelxl.log"
  except:
    command = str(os.path.join(str(args_dict['ccp4_folder']), 'shelxl')) + " sol1 > shelxl.log"
    
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  end_time = time.time()
  
  #" too few to estimate Flack x by" -> broken structure
  #"Message of \"Absolute structure cannot be determined reliably\" was fine for ketone tutorial"
  
  os.chdir(starting_folder_for_shelxl)
  
  write_this = util.show_time(process, start_time, end_time)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
######### end of def run_shelxl_no_cif(args_dict)


def run_shelxl_for_cif(args_dict):
  process = "shelxl (refine the crystal structure along generating cif file (to be opened by UCSF chimera))\n"
  start_time = time.time()
  util.show_header(process)
  
  os.mkdir("shelxl_with_cif")
  
  shutil.copyfile("shelxl_no_cif/sol1.hkl", "shelxl_with_cif/ACTA.hkl")
  
  f_in  = codecs.open("shelxl_no_cif/sol1.ins", 'rb')
  f_out = codecs.open("shelxl_with_cif/ACTA.ins", 'wb')
  for line in f_in:
    if (line[:4].decode('UTF-8') == "L.S."):
      f_out.write(b"ACTA\n")
    f_out.write(line)
  f_out.close()
  f_in.close()
  
  os.chdir("shelxl_with_cif")
  
  try:
    subprocess.check_output(["which", "shelxl"])
    command = "shelxl ACTA > shelxl.log"
  except:
    command = str(os.path.join(str(args_dict['ccp4_folder']), 'shelxl')) + " ACTA > shelxl.log"
    
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  end_time = time.time()
  
  write_this = util.show_time(process, start_time, end_time)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
######### end of def run_shelxl_for_cif(args_dict)

  
def run_shelxt(args_dict, SPACE_GROUP_NUMBER):
  start_time = time.time()
  process = "shelxt (phase the measured intensities)\n"
  util.show_header(process)
  write_this = "cwd:" + str(os.getcwd())
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  write_this = '''
                  -a overrides -g, -h and -w, but not -c or -n; -a without a number is equivalent to -a0.3.
  
                  -y CFOM = CHEM*CC (alternative to default -j1) [off]
  
                  CHEM is a 'chemical' figure of merit that should be between 1.0 (most reasonable) and 0.0 (awful).
 
                  -y is the fraction of bond angles between 95 and 135 degrees ignoring \
                  the 20% highest and 10% lowest peaks. This is only useful for organic \
                  compounds and ligands, not for inorganics, but can be invaluable when \
                  CC and R(weak) fail to distinguish between correct and incorrect P1 solutions.
    
                  shelxt employs a novel dual-space algorithm to solve the phase problem for single-crystal reflection data expanded to the space group P1.
                    (This explanation about shelxt doesn't necessarily mean that this AutoMicroED will use space group P1 though.)
    
                  If successful, different solutions will be named as shelxt_a.res, shelxt_b.res and etc.
                  The solution can be checked by loading the shelxt_a.res in "coot".
                  The shelxt command will have to be repeated until a sensible solution is obtained.'''
  # the last argument is meant for *.ins. For this case shelxt_input_from_xdsconv.ins
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  
  
  ################ <begin> check shelxt path
  try:
    subprocess.check_output(["which", "shelxt"])
    command = "shelxt -a -y -t32 shelxt_input_from_xdsconv"
    # -t32 solves krios problem that uses 64 threads and resulting in error
  except:
    command = str(os.path.join(str(args_dict['ccp4_folder']), 'shelxt')) + " -a -y -t32 shelxt_input_from_xdsconv"
  ################ <end> check shelxt path
  
  
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  
  if (os.path.isfile("shelxt_input_from_xdsconv_a.hkl") == False):
    write_this = "shelxt_input_from_xdsconv_a.hkl not found. shelxt may not have found a satisfactory space group for shelxt_input_from_xdsconv"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    return 0
  end_time = time.time()
  
  write_this = util.show_time(process, start_time, end_time)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  return 1
######### end of def run_shelxt(logfile_name_w_abs_path)


def shelx(args_dict, output_file_name_from_xdsconv):
  util.flog("shelx function for small molecule", args_dict['logfile_name_w_abs_path'])
  
  SPACE_GROUP_NUMBER   = util.retrieve_SPACE_GROUP_NUMBER(args_dict, "XSCALE.LP")
  if (SPACE_GROUP_NUMBER == False):
    return False
    
  UNIT_CELL_CONSTANTS  = util.retrieve_UNIT_CELL_CONSTANTS(args_dict, "XDSCONV.LP")
  # XDSCONV converts reflection data files from xds or xscale into various formats for crystal structure determination like CCP4, or SHELX
  # example: 68.15   169.75   193.81  90.000  90.058  90.000
  # ref:     http://xds.mpimf-heidelberg.mpg.de/html_doc/xds_parameters.html#UNIT_CELL_CONSTANTS=

  print_this = "\t(note) XDSCONV.LP is generated by XDSCONV and reports the results and diagnostics of XDSCONV.\n"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])

  templates_path = args_dict['repo_location'] + "/templates/"
  shelx_template_w_path = os.path.join(templates_path, "shelxt_template.ins")

  shutil.copyfile(shelx_template_w_path, os.path.join(os.getcwd(),"shelxt_template.ins"))
  
  print ("\n\t(note) LATT indicates lattice centering.")
  print ("\n\t\t Its types include 1=P, 2=I, 3=rhombohedral obverse on hexagonal axes, 4=F, 5=A, 6=B, 7=C")
  
  print ("\n\n\t(note) SYMM means symmetry operation (i.e. coordinates of the general positions as given in International Tables. The operator X, Y, Z is always assumed, so may NOT be input. If the structure is centrosymmetric, the origin MUST lie on a center of symmetry.)\n")
  
  if ("Generate_LATT_SYMM_from_website" not in args_dict):
    args_dict['Generate_LATT_SYMM_from_website'] = receive_from_user("Generate_LATT_SYMM_from_website")
    
  if (platform.system() != "Linux"):
    if (str(args_dict['Generate_LATT_SYMM_from_website']).upper() == "TRUE"):
      LATT = LATT_SYMM.retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER)
    else:
      try:
        path = subprocess.check_output(["which", "phenix.python"]).decode('UTF-8')
        print(f"PATH of phenix.python is {path}")
        LATT = LATT_SYMM.retrieve_LATT_SYMM_automatically(SPACE_GROUP_NUMBER, args_dict)
      except:
        util.flog("AutoMicroED can't find/locate phenix.python", args_dict['logfile_name_w_abs_path'])
        util.flog("Please install PHENIX (https://www.phenix-online.org/download/) and add folder that has phenix.python to $PATH", args_dict['logfile_name_w_abs_path'])
        util.flog("\tFor example, the folder that has phenix.python could be /Users/kimd999/bin/phenix-1.18.2-3874/build/bin", args_dict['logfile_name_w_abs_path'])
      
        print_this = "\nUser needs to use https://cci.lbl.gov/cctbx/shelx.html to retrieve LATT and SYMM instead.\n"
        print_this = print_this + "\nPress enter key now.\n"
        if ("kimd999" in home_dir_path):
          nonBlockingRawInput(print_this)
        else:
          input(print_this)
        
        LATT = LATT_SYMM.retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER)


  else: # -> Linux
    if (str(args_dict['Generate_LATT_SYMM_from_website']).upper() == "TRUE"):
      LATT = LATT_SYMM.retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER)
    else:
      LATT_retrieved = False
      try:
        path = subprocess.check_output(["which", "phenix.python"]).decode('UTF-8')
        print(f"PATH of phenix.python is {path}")
        
      except:
        util.flog("\nAutoMicroED can't find/locate phenix.python", args_dict['logfile_name_w_abs_path'])
        util.flog("\nPlease install PHENIX (https://www.phenix-online.org/download/) and add folder that has phenix.python to $PATH", args_dict['logfile_name_w_abs_path'])
        util.flog("\nFor example, the folder that has phenix.python could be /Users/kimd999/bin/phenix-1.18.2-3874/build/bin", \
             args_dict['logfile_name_w_abs_path'])
    
        print_this = "\nUser needs to use https://cci.lbl.gov/cctbx/shelx.html to retrieve LATT and SYMM instead.\n"
        print_this = print_this + "\nPress enter key now.\n"
        
        '''
        if ("kimd999" in home_dir_path):
          nonBlockingRawInput(print_this)
        else:
          input(print_this)
        '''
        
        input(print_this)
        LATT = LATT_SYMM.retrieve_LATT_SYMM_by_website(SPACE_GROUP_NUMBER)
        LATT_retrieved = True
      if (LATT_retrieved == False):
        LATT = LATT_SYMM.retrieve_LATT_SYMM_automatically(SPACE_GROUP_NUMBER, args_dict)
          

  write_SHELX_ins(args_dict, UNIT_CELL_CONSTANTS, LATT)
  
  # if (int(SPACE_GROUP_NUMBER) == 1):
  #   print_this = "shelxt doesn't run for space group=1. Therefore, AutoMicroED will not run shelxt for this space group=1 data."
  #   util.flog(print_this, logfile_name_w_abs_path)
  #   return 0
  # 
  return_from_run_shelxt = run_shelxt(args_dict, SPACE_GROUP_NUMBER) # took 8 seconds on mac, so no need of coding for cascade jobs launching
  if (return_from_run_shelxt == 0):
    exit(1)
  

  run_shelxl_no_cif(args_dict)
  run_shelxl_for_cif(args_dict)
  ### (took 0.3 seconds on mac, so no need of coding for cascade jobs launching)


  #### <begin> organize 
  cwd = os.getcwd()
  util.flog(f"cwd:{cwd}", args_dict['logfile_name_w_abs_path'])
  
  os.chdir("..")

  PATH_per_unit_cell = os.getcwd()
  util.flog(f"PATH_per_unit_cell:{PATH_per_unit_cell}", args_dict['logfile_name_w_abs_path'])
  

  # <begin> move all to intermediate_files folder
  os.mkdir("intermediate_files")

  '''
  # works fine, but generate unncessary warning
  command = "mv * intermediate_files"
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  '''

  all_files_subfolders = os.listdir(path='.')
  all_files_subfolders.remove("intermediate_files")
  for i in range(len(all_files_subfolders)):
    mv_this = all_files_subfolders[i]
    command = "mv " + str(mv_this) + " intermediate_files"
    print (command)
    os.system(command)
  # <end> move all to intermediate_files folder


  command = "cp intermediate_files/shelxl_no_cif/sol1* intermediate_files/shelxl_with_cif/*.cif ."
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)


  os.chdir("../..")
  copy_this_path = os.getcwd()
  util.flog(f"copy_this_path:{copy_this_path}", args_dict['logfile_name_w_abs_path'])

  os.chdir(PATH_per_unit_cell)

  cwd = os.getcwd()
  util.flog(f"cwd:{cwd}", args_dict['logfile_name_w_abs_path'])

  merge_command_indexed = "cat "
  merge_command_notindexed = "cat "
  f_in  = codecs.open("intermediate_files/For_this_SPACE_GROUP_and_UNIT_CELL_merge_these_HKL_by_xscale.txt", 'r')
  for line in f_in:
    util.flog(f"line:{line}", args_dict['logfile_name_w_abs_path'])
    new_folder = os.path.join(copy_this_path.rstrip(), line.rstrip())
    merge_command_indexed = merge_command_indexed + os.path.join(new_folder, "SPOT-indexed.pdb") + " "
    merge_command_notindexed = merge_command_notindexed + os.path.join(new_folder, "SPOT-notindexed.pdb") + " "
  f_in.close()

  merge_command_indexed = merge_command_indexed + " > SPOT-indexed_all.pdb"
  util.flog(merge_command_indexed, args_dict['logfile_name_w_abs_path'])
  os.system(merge_command_indexed)

  merge_command_notindexed = merge_command_notindexed + " > SPOT-notindexed_all.pdb"
  util.flog(merge_command_notindexed, args_dict['logfile_name_w_abs_path'])
  os.system(merge_command_notindexed)

  #### <end> organize 

########### end of def shelx(logfile_name_w_abs_path, repo_location, output_file_name_from_xdsconv)


def write_SHELX_ins(args_dict, UNIT_CELL_CONSTANTS, LATT):
  util.flog("write_SHELX_ins", args_dict['logfile_name_w_abs_path'])
  
  f_in  = codecs.open("shelxt_template.ins", 'r')
  new_shelx_ins_file_name = "shelxt_input_from_xdsconv.ins" # this is a standard SHELX format file
  f_out = codecs.open(new_shelx_ins_file_name, 'w')
  for line in f_in:
    if (line[:4] == "CELL"):
      write_this = "CELL 1.0 " + str(UNIT_CELL_CONSTANTS)
      f_out.write(write_this)
    elif (line[:4] == "LATT"):
      write_this = "LATT " + str(LATT) + "\n"
      f_out.write(write_this)
    elif (line[:4] == "SYMM"):
      if (os.path.isfile("LATT_SYMM.txt") == False):
        LATT_SYMM.enter_SYMM_from_website(home_dir_path, f_out)
      else:
        LATT_SYMM.enter_SYMM_automatically(f_out)
    elif (line[:4] == "SFAC"):
      if "SFAC" not in args_dict:
        args_dict['SFAC'] = receive_from_user("SFAC")
      write_this = "SFAC " + str(args_dict['SFAC']) + "\n"
      f_out.write(write_this)
    elif (line[:4] == "UNIT"):
      if "UNIT" not in args_dict:
        args_dict['UNIT'] = receive_from_user("UNIT")
      write_this = "UNIT " + str(args_dict['UNIT']) + "\n"
      f_out.write(write_this)
    elif (line[:19] == "UNIT_CELL_CONSTANTS"):
      print_this = "\nThe cell constants must meet the requirements implicated by the space group."
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      if "UNIT_CELL_CONSTANTS" not in args_dict:
        args_dict['UNIT_CELL_CONSTANTS'] = receive_from_user("UNIT_CELL_CONSTANTS")
      write_this = "UNIT_CELL_CONSTANTS " + str(args_dict['UNIT_CELL_CONSTANTS']) + "\n"
      f_out.write(write_this)
    else:
      f_out.write(line)
  f_in.close()
  f_out.close()
######## end of def write_SHELX_ins(UNIT_CELL_CONSTANTS, LATT)

