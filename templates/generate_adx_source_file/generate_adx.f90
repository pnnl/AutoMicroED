! Task: generate .adx files from existing XDS.INP and XDS_ASCII.HKL
!       to be able to visualize where XDS finds/expects reflections
! The latest beta versions of ADXV (from http://www.scripps.edu/~arvai/adxv/) 
! can read these .adx files and display them together with the frames.
! Compilation: save this code as "generate_adx.f90" and compile with e.g.
! gfortran -O -C generate_adx.f90 -o generate_adx
! Then move the resulting binary to /usr/local/bin or ~/bin 
! Usage: go to the directory which has XDS_ASCII.HKL and run generate_adx
!
! Kay Diederichs 6/2009
! 
     implicit none
     integer :: hkl(3),iframe,j=-10000,mini=huge(mini),maxi=-huge(maxi),&
                nref=0,i,i1,i2,num
     real intensity,sigi,x,y,z
     character :: string*550,frmnam*512,form*6='(i0.0)'
     logical :: back=.true.

100  format(5i5)
101  format(a)

! find out NAME_TEMPLATE_OF_DATA_FRAMES
     open(1,file='XDS.INP',status='old')
       do
         read(1,101,end=98) string
         string=adjustl(string)
         if (string(:29)=='NAME_TEMPLATE_OF_DATA_FRAMES=') then
           frmnam=adjustl(string(30:))
           i1=index(frmnam,'!')
           if (i1>0) frmnam=frmnam(:i1-1)
           if (index(frmnam,'.',back)>index(frmnam,'?',back)) then
             frmnam=frmnam(:index(frmnam,'.',back))//'adx' ! exchange extension
           else
             frmnam=frmnam(:len_trim(frmnam))//'.adx'  ! add extension
           endif
         endif
       end do
 98  close(1)
     print*,'.adx names :',frmnam(:len_trim(frmnam))
! prepare modification of framename
     i1=index(frmnam,'?')
     i2=0
     do i=i1,len_trim(frmnam)
       if (frmnam(i:i)=='?') then
         i2=i
       else
         exit
       endif
     end do
     if (i2==0) stop 'template should contain a ?'
     write(form(3:3),'(i1)') i2-i1+1
     form(5:5)=form(3:3)

! sort XDS_ASCII.HKL by frame number
     print*,'sorting XDS_ASCII.HKL ...'
     call system('grep -v \! XDS_ASCII.HKL | sort -k 8n > temp_adx.sort')
     open(1,file='temp_adx.sort')
     print*,'sorting XDS_ASCII.HKL done'
     
     num=10000
     do 
       read(1,*,end=99)hkl,intensity,sigi,x,y,z
       iframe=int(z)+1
       mini=min(iframe,mini)
       maxi=max(iframe,maxi)
       nref=nref+1
       if (mod(nref,num)==0) then
         print*,'working',num
         num=num*2
       endif
       if (iframe/=j) then  ! new frame
         write(frmnam(i1:i2),form) iframe
         if (j/=-10000) close(2)
         open(2,file=frmnam)
         j=iframe
       endif
! XDS starts counting at 1, whereas ADXV starts at 0:
       write(string,100) nint(x)-1,nint(y)-1,hkl
       call removeblanks(string)
       write(2,101)string(:len_trim(string))
     end do
 99  print*,'first frame, last frame, nref=',mini,maxi,nref
     close(1,status='delete')
     close(2)
     end      
!
     subroutine removeblanks(string)
! Removes leading and trailing blanks, and turns multiple blanks into one blank.
     implicit none
     character string*(*),copy*132
     integer i,j
     logical first

     j=0
     first=.false.
     do i=1,len_trim(string)
       if (string(i:i) /= ' ') then
         j=j+1
         copy(j:j)=string(i:i)
         first=.true.
       elseif (first) then
         j=j+1
         copy(j:j)=string(i:i)
         first=.false.
       endif
     end do
     string=copy(1:j)
     end
