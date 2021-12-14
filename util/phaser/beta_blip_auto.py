# ref ->https://www.phaser.cimr.cam.ac.uk/index.php/Python_Example_Scripts
# beta_blip_auto.py

from phaser import *
i = InputMR_DAT()
i.setHKLI("beta_blip_P3221.mtz")
i.setHIRES(6.0)
i.setMUTE(True)
r = runMR_DAT(i)
if r.Success():
  i = InputMR_AUTO()
  i.setREFL_DATA(r.getREFL_DATA())
  i.setROOT("beta_blip_auto")
  i.addENSE_PDB_ID("beta","beta.pdb",1.0)
  i.addENSE_PDB_ID("blip","blip.pdb",1.0)
  i.addCOMP_PROT_MW_NUM(28853,1)
  i.addCOMP_PROT_MW_NUM(17522,1)
  i.addSEAR_ENSE_NUM("beta",1)
  i.addSEAR_ENSE_NUM("blip",1)
  i.setMUTE(True)
  del(r)
  r = runMR_AUTO(i)
  if r.Success():
    if r.foundSolutions() :
      print "Phaser has found MR solutions"
      print "Top LLG = %f" % r.getTopLLG()
      print "Top PDB file = %s" % r.getTopPdbFile()
    else:
      print "Phaser has not found any MR solutions"
  else:
    print "Job exit status FAILURE"
    print r.ErrorName(), "ERROR :", r.ErrorMessage()
else:
  print "Job exit status FAILURE"
  print r.ErrorName(), "ERROR :", r.ErrorMessage()