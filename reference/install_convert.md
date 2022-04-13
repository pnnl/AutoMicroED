## Install convert binary
   - convert binary is in [imagemagick](https://imagemagick.org/index.php)
   - This binary is required when AutoMicroED user wants AutoMicroED to estimate ORGX/ORGY automatically from smv input files.
   - A user can prepare this convert binary by full installation of imagemagick [refer](https://imagemagick.org/script/download.php)
   - However, this full installation can be difficult for novices.
   - Therefore, here we share a simpler method of convert preparation below.

### Simple method of convert preparation
   - (at commandline mode)
   - wget https://download.imagemagick.org/ImageMagick/download/binaries/magick .
   - chmod +rwx magick
      - (this change magick file privilege)
   - ./magick
      - (if below error message occurs)
         - dlopen(): error loading libfuse.so.2
         AppImages require FUSE to run.
         You might still be able to extract the contents of this AppImage
         if you run it with the --appimage-extract option.
         See https://github.com/AppImage/AppImageKit/wiki/FUSE
         for more information
      - ./magick --appimage-extract
         - This generates squashfs-root folder
         - Inside this folder, there is convert binary
            - (For example, /squashfs-root/usr/bin/convert)
         - Then add this folder /squashfs-root/usr/bin into user's PATH
         - or specify convert binary by user's args_file
