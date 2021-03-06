## How to prepare to run
   - Generate input image file list.
     - final folder name and each img file name should be same
        - For example, this is correct
           - /gpustorage/MicroEDProc/SMP/CycA_SBGrid/752/112002/img has 112002_0001.img, 112002_0002.img, 112002_0003.img etc
        - This is wrong
           - /gpustorage/MicroEDProc/SMP/CycA_SBGrid/752/20181220-112002/img has 112002_0001.img, 112002_0002.img, 112002_0003.img etc
     - Refer (AutoMicroED git repository)/templates/input_files for
        - user_provided_individual_mrc
        - user_provided_mrcs
        - user_provided_smv
     - This kind of mrc list file can be generated by iterating mrc file names
        - (for example), ls $PWD/\*/crystal\*/\*/\*.mrc > mrc_list.txt
           - (linux 101) '$PWD' prints full path until current working directory
           - (linux 101) '>' saves all printout from previous command to a specified file (in this example, mrc_list.txt)
           - (linux 101) '\*' deals all filenames. '\*.mrc' deals all filenames that end with .mrc
        - (note) The filename and extention for this "mrc_list_file" can be any as user prefers. For example, you are welcome to name as 2021_June_mrc.list instead. Just specify your mrc_list filename when you launch AutoMicroED
     - By default, right after krios, input mrc is in single frame (e.g. it does not have stack).
        - AutoMicroED catches common filenames then.
        - (For example), when user specified
           - /home/KL/single_frames/merge_2/crystal_6/2021-03-03-133857/2021-03-03-133857_0199.mrc
           - /home/KL/single_frames/merge_2/crystal_6/2021-03-30-142654/2021-03-30-142654_0200.mrc
        - in mrc_list.txt, then AutoMicroED uses all 2021-03-03-133857_????.mrc and 2021-03-30-142654_????.mrc files
     - If a user prefers, stack mrc files can be entered to AutoMicroED instead.
        - Stack can be made by eman2 (which should be installed aside from this AutoMicroED)
           - 'e2proc2d.py (file names of each mrc) (file name of merged mrcs)'
           - (For example,) 'e2proc2d.py *_each.mrc merged.mrcs'
              - (File name of merged mrcs) should have .mrcs extension for proper eman2 handling
           - This eman2 operation needs proper eman2 environement setting (e.g. ~/.bashrc which is updated by eman2 installation)
        - Then, let mrc_list.txt contains merged mrcs files.
           - (For example mrc_list.txt has)
              - /home/KL/single_frames/merge_2/crystal_6/2021-03-03-133857/2021-03-03-133857.mrcs
              - /home/KL/single_frames/merge_2/crystal_6/2021-03-30-142654/2021-03-30-142654.mrcs
   - Understand convenient argument file.
      - Refer (git repo)/templates/input_files/explanation
      - If parameters are specified in an argument file, then manual specification of those parameters is bypassed.
      - See working examples at (git repo)/templates/args_file/example
   - Understand XDS_parameter file.
      - Refer (git repo)/templates/XDS_param_explanation.INP
   - Copy mrc file to working directory
      - (linux 101) ls *.mrc | wc -l shows number of mrc files in a folder
      - Then, tmux to allow offline copying
      - Then, copy for example
         - rsync -aPuv (source folder) kimd999@kriosgpu.emsl.pnl.gov:~/(target folder)
         - (or) scp -r (source folder) kimd999@kriosgpu.emsl.pnl.gov:~/(target folder)
