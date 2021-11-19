## For small molecule after merging XDS_ASCII.HKL files 
   - shelxt 
      - function: phase the measured intensities
      - reference: http://journals.iucr.org/a/issues/2015/01/00/sc5086/index.html
   - shelxl 
      - function: refine the crystal structure
      - input:  sol1.ins, sol1.hkl, ACTA.ins, ACTA.hkl
      - output: sol1.fcf, sol1.res, ACTA.cif
   - Analyze/visualize results
      - [link](./reference/analyze_small_molecule_result.md)
