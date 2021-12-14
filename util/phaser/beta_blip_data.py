# ref ->https://www.phaser.cimr.cam.ac.uk/index.php/Python_Example_Scripts
# beta_blip_data.py

from phaser import *
i = InputMR_DAT()
HKLIN = "beta_blip_P3221.mtz"
i.setHKLI(HKLIN)
i.setMUTE(True)
r = runMR_DAT(i)
print r.logfile()
if r.Success():
  hkl = r.getMiller()
  fobs = r.getF()
  sigma = r.getSIGF()
  nrefl = min(10,hkl.size())
  print "Data read from: " , HKLIN
  print "First ", nrefl , " reflections"
  print "%4s %4s %4s %10s %10s" % ("H","K","L",F,SIGF)
  for i in range(0,nrefl):
    print "%4d %4d %4d %10.4f %10.4f" % \
      (hkl[i][0],hkl[i][1],hkl[i][2],fobs[i],sigma[i])
else:
  print "Job exit status FAILURE"
  print r.ErrorName(), "ERROR :", r.ErrorMessage()