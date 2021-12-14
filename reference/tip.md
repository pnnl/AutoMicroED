## Tip
   -  Please do not copy run_all.py only into some folder, and run there (e.g. use run_all.py as in original location of git clone)
      - For example, if a user git cloned at
         - ~/script/python/cryoEM/AutoMicroED
            - do
               - python ~/script/python/cryoEM/AutoMicroED/run_all.py
   - If a user prefers, the user can add 
         - alias MicroED="python /Users/kimd999/script/python/cryoEM/AutoMicroED/run_all.py"
      - in ~/.bash_profile
      - and source ~/.bash_profile
      -  then simply run as
         - MicroED
   - If a user wants to update code, do
      - git pull
      - at (git repo), for example ~/script/python/cryoEM/AutoMicroED
      - this update of code is not necessary right after git clone
   - Consult with reference/microED_notes.pdf file for abbreviations and additional options.
   - For catalase, carbamazepine microED data generation (perhaps for other targets as well), rotation rate of the stage is better to be <= 0.5 degree/second for enough sampling. 1 degree/second is too sparse.
   - imod's header shows stack number
      - (For example, in PNNL_krios_GPU server) source /home/kimd999/.bashrc_IMOD
      - then 'header (merged mrcs)'
      - For example, if 'header merged.mrcs' shows
         - Number of columns, rows, sections .....    4096    4096     147
      - this mrcs has 147 images (e.g. I merged 71 and 76 images)

## Tip for PNNL only
   -  When running on PNNL laptop, make sure that you do your processing not on Desktop. OneDrive sync causes issues.
      - Recommended path: Any path except that has space ( ) in path or too long path name.
   -  When running on PNNL_HPC_Cascade, please contact us first to allocate charging account.

## Confirmed operating system
   - MacOS
   - Linux
   - WindowsOS may not work since there is no guarantee that third party software will work for WindowsOS (e.g. tvips-tools-jiffies, xds)
   - Supports CPU only

## Troubleshooting
   - [link](./reference/troubleshooting.md)
