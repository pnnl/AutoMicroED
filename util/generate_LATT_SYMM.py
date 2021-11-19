# Thanks to Billy Poon who provided initial code of this

from cctbx.sgtbx import space_group_info
import os, sys

def LATT_SYMM_DN(space_group, decimal=False):
    output_file_name = "LATT_SYMM.txt"
    if (os.path.isfile(output_file_name) == True):
        os.remove(output_file_name)
    f_out = open (output_file_name, "a")
    Z = space_group.conventional_centring_type_symbol()
    
    Z_dict = {
      "P": 1,
      "I": 2,
      "R": 3,
      "F": 4,
      "A": 5,
      "B": 6,
      "C": 7,
    }
    
    try:
      LATT_N = Z_dict[Z]
    except Exception:
      raise RuntimeError("Error: Lattice type not supported by SHELX.")
    
    # N must be made negative if the structure is non-centrosymmetric.
    if (space_group.is_centric()):
      if (not space_group.is_origin_centric()):
        raise RuntimeError("Error: " \
          + " SHELX manual: If the structure is centrosymmetric, the" \
          + " origin MUST lie on a center of symmetry.")
    else:
      LATT_N = -LATT_N;
    write_this = str(LATT_N) + "\n"
    f_out.write(write_this)
    
    # The operator x,y,z is always assumed, so MUST NOT be input.
    for i in range(1, space_group.n_smx()):
      SYMM = space_group(i).as_xyz(
        decimal=decimal,
        t_first=False,
        symbol_letters="XYZ",
        separator=",")  + "\n"
      f_out.write(SYMM)  
    f_out.close()
############## end of def LATT_SYMM_DN(space_group, decimal=False)


if (__name__ == "__main__") :
    args = sys.argv[0:]    
    SPACE_GROUP_NUMBER = int(args[1])

    sgi = space_group_info(SPACE_GROUP_NUMBER)
    sg = sgi.group()
    latt = sg.conventional_centring_type_symbol()

    LATT_SYMM_DN(sg, decimal=False)
    