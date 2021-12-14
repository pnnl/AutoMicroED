import glob
edit = -4
for pdb_file in glob.glob("*.pdb"):
    print (pdb_file)
    with open(pdb_file) as f_in:
        out_file = pdb_file[:edit] + '_no_HETATM.pdb'
        with open(out_file, "w") as f_out:
            for line in f_in:
                if line[:6] != "HETATM":
                    f_out.write(line)
    
