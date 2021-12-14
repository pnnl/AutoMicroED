#''beta_blip_auto.com''
# ref: https://www.phaser.cimr.cam.ac.uk/index.php/Keyword_Example_Scripts
phaser << eof
TITLe beta blip automatic
MODE MR_AUTO
HKLIn beta_blip.mtz
LABIn F=Fobs SIGF=Sigma
ENSEmble beta PDB beta.pdb IDENtity 100
ENSEmble blip PDB blip.pdb IDENtity 100
COMPosition PROTein SEQuence beta.seq NUM 1 #beta
COMPosition PROTein SEQuence blip.seq NUM 1 #blip
SEARch ENSEmble beta NUM 1
SEARch ENSEmble blip NUM 1
ROOT beta_blip_auto # not the default
eof
