import glob, os, shutil

for each_file_name in glob.glob("093757merged_*"):
    new_file_name = each_file_name + ".adx"
    cmd = "mv " + str(each_file_name) + " " + str(new_file_name)
    print (cmd)
    os.system(cmd)
