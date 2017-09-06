# !/usr/bin/env python
#run example
#exec(open('/data/scripts/process_bids/run_vbm_bids.py').read())
#run_vbm_bids('/data/bids_input','/data/bids_output')




import glob, os,sys
import nibabel as nib

#Arguments passed to the vbm script from coinstac
input_path=str(sys.argv[1])
coinstac_tmp_path=str(sys.argv[2])

# Setting the parameters from collected arguments
in_bids_path = input_path
smri_data=glob.glob(in_bids_path+'/sub*/anat/*T1w*.nii.gz')
out_path=coinstac_tmp_path

# Make sure all the data in shared folder is rwx
# Check if input is BIDS , if not show the error
# Check if there are rwx permissions to output_path

# Create directory to write vbm outputs to
if not os.path.exists(out_path):
    os.makedirs(out_path)

#Create a readme.txt file to point to input data,date and time, and other useful info. down the line

# if input data is in BIDS, then extract sub name and nii.gz files
for gz in smri_data:
    anat_dir=('/').join(gz.split('/')[0:-1]) # MAKE SURE THAT ANAT IS BIDS STANDARD NAME FOR SMRI
    sub_id=gz.split('/')[-3]

    vbm_out = out_path + '/' + sub_id + '/anat'

    nii_output = (gz.split('/')[-1]).split('.gz')[0]

    # Create output dir for sub_id
    if not os.path.exists(vbm_out):
        os.makedirs(vbm_out)

    #gunzip *T1w*.gz files
    n1_img = nib.load(gz)
    nib.save(n1_img, vbm_out+'/'+nii_output)


    nifti_file=vbm_out+'/'+nii_output

    print(vbm_out)
    print(nifti_file)

    from nipype.interfaces.spm.utils import DicomImport, ApplyTransform
    from nipype.interfaces.spm import NewSegment, Smooth
    from nipype.interfaces.io import DataSink
    from nipype.interfaces.utility import Function
    import nipype.pipeline.engine as pe
    import glob, json, os, sys, argparse
    import corr
    import sys

    # Connect spm12 standalone to nipype
    from nipype.interfaces import spm

    matlab_cmd = '/opt/spm12/run_spm12.sh /opt/mcr/v92 script'
    spm.SPMCommand.set_mlab_paths(matlab_cmd=matlab_cmd, use_mcr=True)

    # Test whether spm version is printed to the screen
    spm.SPMCommand().version

    # Setting the parameters from collected arguments

    transf_mat_path = '/data/mat_file/transform.mat'
    tpm_path = '/data/tpm_file/TPM.nii'

    #Create vbm_spm12 dir
    if not os.path.exists(vbm_out+"/vbm_spm12"):
        os.makedirs(vbm_out+"/vbm_spm12")

    # Reorientation node and settings
    reorient = pe.Node(interface=ApplyTransform(), name='reorient')
    reorient.inputs.mat = transf_mat_path
    reorient.inputs.in_file = nifti_file
    reorient.inputs.out_file = vbm_out + "/vbm_spm12/Re.nii"

    # Segementation Node and settings
    segmentation = pe.Node(interface=NewSegment(), name='segmentation')
    segmentation.inputs.channel_info = (0.0001, 60, (False, False))
    Tis1 = ((tpm_path, 1), 1, (True, False), (True, True))
    Tis2 = ((tpm_path, 2), 1, (True, False), (True, True))
    Tis3 = ((tpm_path, 3), 2, (True, False), (True, True))
    Tis4 = ((tpm_path, 4), 3, (True, False), (True, True))
    Tis5 = ((tpm_path, 5), 4, (True, False), (True, True))
    Tis6 = ((tpm_path, 6), 2, (True, False), (True, True))
    segmentation.inputs.tissues = [Tis1, Tis2, Tis3, Tis4, Tis5, Tis6]

    # Function & Node to transform the list of normalized class images to a compatible version for smoothing
    def transform_list(normalized_class_images):
        return [each[0] for each in normalized_class_images]

    list_normalized_images = pe.Node(interface=Function(input_names='normalized_class_images', \
                                                        output_names='list_norm_images', function=transform_list), \
                                     name='list_normalized_images')

    # Smoothing Node & Settings
    smoothing = pe.Node(interface=Smooth(), name='smoothing')
    smoothing.inputs.fwhm = [10, 10, 10]

    # Datsink Node that collects segmented, smoothed files and writes to out_path
    datasink = pe.Node(interface=DataSink(), name='sinker')
    datasink.inputs.base_directory = vbm_out

    # Workflow and it's connections
    vbm_preprocess = pe.Workflow(name="vbm_preprocess")
    vbm_preprocess.connect([(reorient, segmentation, [('out_file', 'channel_files')]), \
                            (segmentation, list_normalized_images,
                             [('normalized_class_images', 'normalized_class_images')]), \
                            (list_normalized_images, smoothing, [('list_norm_images', 'in_files')]), \
                            (segmentation, datasink,
                             [('modulated_class_images', 'vbm_spm12'), ('native_class_images', 'vbm_spm12.@1'), \
                              ('normalized_class_images', 'vbm_spm12.@2'), ('transformation_mat', 'vbm_spm12.@3')]), \
                            (smoothing, datasink, [('smoothed_files', 'vbm_spm12.@4')])])

    try:
        # Run the workflow
        sys.stderr.write("running vbm workflow")
        res = vbm_preprocess.run()

    except:
        # If fails raise the excpetion and set status False
        status = False

    else:
        # If succeeds, set status True
        status = True

    finally:
        # Finally , write the status to .json object and calculate correlation coefficent
        segmented_file = glob.glob(vbm_out + "/vbm_spm12/swc1*nii")
        corr_value = corr.get_corr(tpm_path, segmented_file[0])
        sys.stdout.write(json.dumps({"vbm_preprocess": status}, sort_keys=True, indent=4, separators=(',', ': ')))

    print('running')



