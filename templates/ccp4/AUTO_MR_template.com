phaser << eof

MODE MR_AUTO

HKLIN catalase.mtz

LABIN F = FP SIGF = SIGFP

ENSEMBLE target PDBFILE 8cat_no_HETATM.pdb IDENTITY 0.95
	      
COMPOSITION PROTEIN SEQUENCE catalase.dat NUM 4

SEARCH ENSEMBLE target NUM 2

ROOT AUTO_target

eof
