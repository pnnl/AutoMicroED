from datetime import datetime as dt
from math import isclose
import argparse, codecs, glob, os, platform, random, shutil, signal, subprocess, sys, time
import mrc2smv, protein, shelx, xds, xscale
import util


def xdsconv(args_dict):
  
  process = "xdsconv"
  start_time = time.time()
  util.show_header(process)
  
  templates_path = args_dict['repo_location'] + "/templates/"
  XDSCONV_template_INP_w_path = os.path.join(templates_path, "XDSCONV_template.INP")
  
  print_this = "\t(note) XDSCONV.INP contains the input parameters (see section Input Parameters) you have to provide to run the program. This file is mandatory and must reside in the current directory from which XDSCONV is called.\n"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
  
  if os.path.isfile("XDS_ASCII_merged.hkl") == False:
    util.flog("XDS_ASCII_merged doesn't exist in this folder", args_dict['logfile_name_w_abs_path'])
    flog_wo_print("XDS_ASCII_merged doesn't exist in this folder", args_dict['summary_logfile_name_w_abs_path'])
    return False, False
  
  f_in  = codecs.open(XDSCONV_template_INP_w_path, 'r')
  new_XDSCONV_INP_file_name = "XDSCONV.INP"
  f_out = codecs.open(new_XDSCONV_INP_file_name, 'w')
  
  for line in f_in:
    if (line[:11] == "INPUT_FILE="):
      write_this = "INPUT_FILE=XDS_ASCII_merged.hkl\n"
      f_out.write(write_this)
    elif (line[:12] == "OUTPUT_FILE="):
      if ('protein' in args_dict.keys()):
        if (
           (str(args_dict['protein']).upper() == "TRUE")
           or (str(args_dict['protein']).upper() == "T")
           ) :
          output_file_name_from_xdsconv = "ready_for_f2mtz.hkl"
          write_this = "OUTPUT_FILE=" + str(output_file_name_from_xdsconv) + " CCP4_I+F\n"
          #https://smb.slac.stanford.edu/facilities/software/xds/
        else:
          output_file_name_from_xdsconv = "shelxt_input_from_xdsconv.hkl"
          write_this = "OUTPUT_FILE=" + str(output_file_name_from_xdsconv) + " SHELX !CCP4_I+F ! or CCP4_I or CCP4_F or SHELX or CNS\n"
      else:
        print ("Please specify whether this is for protein")
        args_dict['protein'] = receive_from_user("protein")
        if (
           (str(args_dict['protein']).upper() == "TRUE")
           or (str(args_dict['protein']).upper() == "T")
           ) :
          output_file_name_from_xdsconv = "ready_for_f2mtz.hkl"
          write_this = "OUTPUT_FILE=" + str(output_file_name_from_xdsconv) + " CCP4_I+F\n"
          #https://smb.slac.stanford.edu/facilities/software/xds/
        else:
          output_file_name_from_xdsconv = "shelxt_input_from_xdsconv.hkl"
          write_this = "OUTPUT_FILE=" + str(output_file_name_from_xdsconv) + " SHELX !CCP4_I+F ! or CCP4_I or CCP4_F or SHELX or CNS\n"
      f_out.write(write_this)
    else:
      f_out.write(line)
  f_in.close()
  f_out.close()

    
  if (
       (str(args_dict['protein']).upper() == "TRUE") 
       or (str(args_dict['protein']).upper() == "T")
     ):
    print_this = " XDSCONV will now generate the keyworded input file F2MTZ.INP needed by f2mtz for the final conversion to binary MTZ-format."
    '''
     ref. https://xds.mr.mpg.de/html_doc/xdsconv_formats.html
     XDSCONV will now generate the keyworded input file F2MTZ.INP
     needed by f2mtz for the final conversion to binary MTZ-format.
     To run the CCP4 programs f2mtz and cad (to convert indices to
     the CCP4-asymmetric unit), just type the two commands:

     f2mtz HKLOUT temp.mtz<F2MTZ.INP
     cad HKLIN1 temp.mtz HKLOUT output_file_name.mtz<<EOF
     LABIN FILE 1 ALL
     DWAVELENGTH FILE 1 1    0.01960
     END
     EOF'''
  else:
    print_this = " xdsconv will convert reflection data file (XDS_ASCII_merged.hkl) to hkl (shelxt_input_from_xdsconv.hkl)"
  util.flog(print_this, args_dict['logfile_name_w_abs_path'])
    
    
  command = "xdsconv "
  print (command)
  os.system(command)   # took < 0.5 second, no need of linux job launching
  end_time = time.time()
  
  if (os.path.isfile(output_file_name_from_xdsconv) == False):
    write_this = str(output_file_name_from_xdsconv) + " is not generated. Exit now.\n"
    util.flog(write_this, args_dict['logfile_name_w_abs_path'])
    return False, output_file_name_from_xdsconv
  
  write_this = util.show_time(process, start_time, end_time)
  util.flog(write_this, args_dict['logfile_name_w_abs_path'])
  return True, output_file_name_from_xdsconv
############ end of def xdsconv(logfile_name_w_abs_path, repo_location):
