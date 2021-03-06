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
      - Usage: 'header (mrcs filename)'
      - For example, if 'header merged.mrcs' shows
         - Number of columns, rows, sections .....    4096    4096     147
      - this mrcs has 147 images (e.g. I merged 71 and 76 images)

## Tip for File System Path
   -  run AutoMicroED on path that has no space ( ) in it.
      - For example, do not run AutoMicroED at "Desktop" or "OneDrive sync" since often these have () in PATH.
   - Also, do not run AutoMicroED at a folder has too long path name (most operating systems cannot handle properly).


## Troubleshooting of xds
   - [link](./troubleshooting.md)
