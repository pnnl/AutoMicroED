from datetime import datetime as dt
import codecs, glob, os, shutil, subprocess, sys, time
import util

try:
  from envbash import load_envbash
except:
  print ("envbash not found, install it by typing")
  print ("\tpip install envbash")
  print ("\tReference: https://pypi.org/project/envbash/")
  exit(1)


def cad(args_dict):
  '''
  # 2nd xscale should have merged XDS_ASCII.HKL files by now
  print_this = "\t(note) Collect and sort crystallographic reflection data from several files, to generate a single set.\n"
  print_this = print_this + "\t Merge mtz files.\n"
  flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  try:
    subprocess.check_output(["which", "cad"])
    command = "cad HKLIN1 from_f2mtz.mtz HKLOUT from_f2mtz_cad.mtz<<EOF"
  except:
    command = str(os.path.join(str(args_dict['ccp4_folder']), 'cad')) + " HKLIN1 from_f2mtz.mtz HKLOUT from_f2mtz_cad.mtz<<EOF"
  
  flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  '''
#######def cad(logfile_name_w_abs_path, args_dict):
  

def f2mtz(args_dict):
  print_this = "AutoMicroED will run f2mtz to convert a free- or fixed-format formatted reflection file to MTZ format. It should be used on merged data in the later st\
ages of structure determination."
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  try:
    subprocess.check_output(["which", "f2mtz"])
    f2mtz_command = "f2mtz hklin ready_for_f2mtz.hkl hklout from_f2mtz.mtz<F2MTZ.INP"
  except:
    f2mtz_command = str(os.path.join(str(args_dict['ccp4_folder']), 'f2mtz')) + " HKLOUT from_f2mtz.mtz<F2MTZ.INP"
  
  util.flog(f2mtz_command, args_dict['logfile_name_w_abs_path'])
  #util.flog_wo_print(f2mtz_command, args_dict['summary_logfile_name_w_abs_path'])
  
  os.system(f2mtz_command)
  
  if os.path.isfile("from_f2mtz.mtz") == False:
    print_this = "f2mtz did't work maybe because of \"f2mtz:  Cannot open environ.def\""
    print_this = print_this + ".\nTherefore, AutoMicroED will source ccp4.setup-sh.in and try again."
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    
    ####### <begin> generate ccp4.setup-sh_new.in
    if ('ccp4_folder' not in args_dict.keys()):
      print_this = "\nccp4_folder (full PATH that has ccp4 binaries) is not defined in args_file\n"
      print_this = print_this + "Either specify it args_file (for later AutoMicroED run)\n"
      print_this = print_this + "or enter a full PATH of ccp4_folder now (for example /opt/apps/ccp4-7.1/bin)."
      print_this = print_this + "\n\tRefer (git repo)/templates/args_file/explanation_of_args.txt for an example of ccp4_folder"
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      ccp4_folder = receive_from_user("ccp4_folder")
      args_dict['ccp4_folder'] = ccp4_folder

    print_this = "ccp4_folder:" + str(args_dict['ccp4_folder'])
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])


    splited = args_dict['ccp4_folder'].split("/")
    
    CCP4_MASTER = ''
    CCP4_folder_basename = ''
    for i in range (len(splited)):
        if "ccp4" in splited[i]:
            CCP4_folder_basename = splited[i]
            break
        CCP4_MASTER = CCP4_MASTER + str(splited[i]) + "/"
    CCP4_MASTER = CCP4_MASTER.rstrip()

    f_in  = codecs.open(os.path.join(str(args_dict['repo_location']), "templates", "ccp4", "ccp4.setup-sh.in"), 'r')
    f_out = codecs.open("ccp4.setup-sh_new.in", "w")
    for line in f_in:
      if (str(line[:19]) == "export CCP4_MASTER="):
        new_line = "export CCP4_MASTER=" + str(CCP4_MASTER) + "\n"
        f_out.write(new_line)
      elif (str(line[:12]) == "export CCP4="):
        new_line = "export CCP4=$CCP4_MASTER/" + str(CCP4_folder_basename)
        f_out.write(new_line)
      else:
        f_out.write(line)
    f_in.close()
    f_out.close()
    
    command = "chmod +rwx ccp4.setup-sh_new.in"
    util.flog(command, args_dict['logfile_name_w_abs_path'])
    os.system(command)
    ####### <end> generate ccp4.setup-sh_new.in
    
    
    cwd = os.getcwd()
    print_this = "Current working directory for f2mtz: " + str(cwd)
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    in_w_path = os.path.join(str(cwd), "ccp4.setup-sh_new.in")
    command = "load_envbash " + str(in_w_path)
    util.flog(command, args_dict['logfile_name_w_abs_path'])
    load_envbash(in_w_path)
    
    util.flog(f2mtz_command, args_dict['logfile_name_w_abs_path'])

    try:
      os.system(f2mtz_command)
      return True
    except:
      return False
    
#######def f2mtz(logfile_name_w_abs_path, args_dict):



def phaser_mr(args_dict):
  print_this = "phaser mr"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])

  f_template = open(os.path.join(args_dict['repo_location'], 'templates', 'ccp4', 'AUTO_MR_template.com'), 'r')
  f_com = open('AUTO_MR.com', 'w')
  for line in f_template:
    if (line[:6] == "phaser"):
      # phenix.phaser doesn't work, phenix.phaser_1.19.2-4158 works
      path = subprocess.check_output(["which", "phenix.phaser"]).decode('UTF-8')
      print_this = "\tPath of phenix.phaser:" + str(path)
      util.flog(print_this, args_dict['logfile_name_w_abs_path'])
      splited_path = path.split('/')
      for i in range(len(splited_path)):
        if "phenix-" in splited_path[i]:
          phenix_ver = splited_path[i].split('phenix-')[1]
          break
      
      new_line = "{} << eof\n".format("phenix.phaser_"+str(phenix_ver))
      f_com.write(new_line)
    elif (line[:28] == "COMPOSITION PROTEIN SEQUENCE"):
      new_line = "COMPOSITION PROTEIN SEQUENCE " + args_dict['COMPOSITION_PROTEIN_SEQUENCE'] + " NUM " \
                 + args_dict['COMPOSITION_PROTEIN_SEQUENCE_NUM'] + " \n"
      f_com.write(new_line)
    elif (line[:5] == "HKLIN"):
      new_line = "HKLIN from_f2mtz.mtz\n"
      f_com.write(new_line)
    elif (line[:23] == "ENSEMBLE target PDBFILE"):
      new_line = "ENSEMBLE target PDBFILE " + args_dict['ENSEMBLE_PDBFILE'] + " IDENTITY " \
                + args_dict['ENSEMBLE_PDBFILE_IDENTITY'] + "\n"
      f_com.write(new_line)
    elif (line[:22] == "SEARCH ENSEMBLE target"):
      new_line = "SEARCH ENSEMBLE target NUM " + args_dict['SEARCH_ENSEMBLE_NUM'] + " \n"
      f_com.write(new_line)
    else:
      f_com.write(line)
  f_com.close()
  f_template.close()
  
  command = "chmod +rwx AUTO_MR.com"
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  
  cwd = os.getcwd()
  print_this = "Current working directory for phaser_mr: " + str(cwd)
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  run_this = os.path.join(cwd,"AUTO_MR.com")
  command = "source " + str(run_this)
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  
  if (os.path.isfile("AUTO_target.sol") == False):
    print_this = "phaser MR failed (e.g. AUTO_target.sol is not generated.)\n"
    print_this = print_this + "maybe because of \"FATAL RUNTIME ERROR: The composition entered will not fit in the unit cell volume\"?\n"
    print_this = print_this + "This kind of error occurred when input pdb and input mtz were not corresponding.\n"
    print_this = print_this + "Refer https://www.phaser.cimr.cam.ac.uk/index.php/Molecular_Replacement"
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
    return False
  else:
    return True
##### end of def phaser_mr(args_dict):



def phenix_refine_fn(args_dict):
  print_this = "phenix.refine after phaser MR per each same SPACE GROUP and similar UNIT_CELL"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  if (os.path.isfile("from_f2mtz.mtz") == False):
    print_this = "from_f2mtz.mtz doesn't exist. Therefore, phenix.refine will not run. Please check whether phenix.phaser MR properly."
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    return False

  command = "phenix.refine {} {} input.xray_data.labels=IMEAN input.xray_data.r_free_flags.generate=True"\
            .format("from_f2mtz.mtz", "AUTO_target.1.pdb")
  util.flog(command, args_dict['logfile_name_w_abs_path'])
  os.system(command)
  
  see_R_free_R_work(args_dict)
  return True
######### end of def phenix_refine_fn(args_dict):  



def see_LLG_TFZ(args_dict):
  f_in  = open("AUTO_target.sol", 'r')
  for line in f_in:
    splited_line = line.split()
    for i in range(len(splited_line)):
      if (splited_line[i][:4] == "LLG="):
        LLG = splited_line[i][4:]
      if (splited_line[i][:5] == "TFZ=="):
        TFZ = splited_line[i][5:]

  f_in.close()
  
  print_this = "\t\tLLG:" + str(LLG)
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])

  if float(LLG) < 0:
    print_this = "\t\t\tLLG (log-likelihood gain) < 0. Therefore, phaser MR needs to be ran with a different approach."
    print_this = print_this + "Refer https://www.phaser.cimr.cam.ac.uk/index.php/Molecular_Replacement"
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
  
  print_this = "\t\tTFZ:" + str(TFZ)
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])

  if float(TFZ) < 8:
    print_this = "\t\t\tTFZ (translation function z-score) < 8.\n"
    print_this = print_this + "\t\t\tTherefore, phaser MR needs to be ran with a different approach.\n"
    print_this = print_this + "\t\t\tFor a translation function, the correct solution will generally have a Z-score (TFZ) over 5 and be well separated from the rest of the solutions.\n"
    print_this = print_this + "\t\t\tRefer https://www.phaser.cimr.cam.ac.uk/index.php/Molecular_Replacement"
    util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
    
  if float(LLG) < 0 or float(TFZ) < 8:
    return False
  else:
    return True
########################## end of def see_LLG_TFZ(args_dict):


def see_R_free_R_work(args_dict):
  search_this = os.path.join("*.refine_001.log")
  refine_log_found = False
  for log_name_from_phenix_refine in glob.glob(search_this): # this glob pick file randomly
    refine_log_found = True
    f_in  = open(log_name_from_phenix_refine, 'r')
    for line in f_in:
      splited_line = line.split()
      if (len(splited_line) == 7):
        if (splited_line[0] == "Final"):
          print_this = "{}".format(line)
          util.flog(print_this, args_dict['logfile_name_w_abs_path'])
          util.flog_wo_print(print_this, args_dict['summary_logfile_name_w_abs_path'])
          #R_work = splited_line[3]
          #R_free = splited_line[6]
    break
  if (refine_log_found == True):
    f_in.close()
########################## end of def see_R_free_R_work(args_dict):
