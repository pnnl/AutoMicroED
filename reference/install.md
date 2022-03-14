## How to install
   - (at commandline) git clone https://github.com/pnnl/AutoMicroED.git
      - (This git clone is required only once. This does not need to be repeated everytime a user needs to run AutoMicroED.)
   - Install (once)
      - For more efficient library management (do not complicate other environments), we recommend 
         - install conda from https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
         - conda activate (conda name) 
         - then, install below.
      - However, it is fine to install without conda environment management.
         - pip install -r <user path>/requirements.txt
         - compile generate_adx (optional)
            - [copy generate_adx_source_file to user's folder](https://strucbio.biologie.uni-konstanz.de/xdswiki/index.php/Generate_adx)
            - gfortran -O -C generate_adx.f90 -o generate_adx
      - Estimated install time: 5 minutes with fresh conda environment set-up. Less time without conda set-up.


### Make sure needed third party software are installed 
   - [Refer](./third_party_sw.md)
      - (Some software may not be installed in WindowsOS.)
      - Designate PATH for tvips, XDS and ccp4
         - For example, for bash user
            - In macOS
               - export PATH="/Users/kimd999/research/microED/dn_try/tvips-tools-jiffies-20191209-macos64/":$PATH
               - export PATH="/Users/kimd999/bin/XDS-OSX_64/":$PATH
               - export PATH="/Applications/ccp4-7.0/bin/":$PATH


### Git troubleshooting
   - If user's OS doesn't have git
      - [Install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
   - If a user sees the error message during git clone, “Permission denied (publickey).fatal: Could not read from remote repository. Please make sure you have the correct access rights and the repository exists.”,
      - User’s computer needs to be registered to his/her github account.
      - Therefore, make/log in github account (free).
      - [Generate a new SSH key](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) 
      - [Add a new SSH key to your GitHub account](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
   - If user's macOS shows, “xcode-select: note: no developer tools were found at '/Applications/Xcode.app', requesting install. Choose an option in the dialog to download the command line developer tools.”
      - Download commandline as instructed (this may take ~7 minutes)
