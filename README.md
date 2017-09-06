# VBM_pre-processing_pipeline
This code takes input structural MRI nifti(*.nii) files in BIDS format and runs Voxel Based Morphometry(VBM) on them. The outputs are Registered (to SPM template)segmented images (wc1*.niii-white matter, wc2*.nii-gray matter, wc3*.nii-cerebro spinal fluid)

# To run the code
run the script run_vbm_bids.py and pass two command line arguments 
1st arg-Path to BIDS directory , where the script can find structural MRI nii files for various subjects
2nd arg-Temperary path where the output should be written to

EX:
python3 "/data/scripts/process_bids/run_vbm_bids.py" '/data/scripts/process_bids/bids_input' '/data/scripts/process_bids/bids_output'
