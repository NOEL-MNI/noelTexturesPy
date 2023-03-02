# Focal Cortical Dysplasia Texture Pipeline

This current site documents the instructions for installing and using the texture pipeline developed at the Neuroimaging of Epilepsy Laboratory ([https://noel.bic.mni.mcgill.ca](https://noel.bic.mni.mcgill.ca/)). 

noelTexturesPy generates 3D volume-based *Relative Intensity* and *Gradient* *Magnitude* maps derived from 3D T1-weighted MRI with isotropic resolution for computer-aided detection of focal cortical dysplasia (FCD).


!!! WARNING "Disclaimer"

    1. This pipeline should be used only when a focal cortical dysplasia type II is suspected. It is [not recommended]{.underline} to use this pipeline for the detection of any other epileptogenic lesions, such as hippocampal sclerosis, heterotopias or tumors.

    2. The use of this pipeline for clinical decision-making is not the responsibility of NOEL. The intended use is solely the responsibility of the operator.

    3. Before you make use of the pipeline, please read the paper that describes the methodology and the interpretation: "Texture analysis and morphological processing of magnetic resonance imaging assist detection of focal cortical dysplasia in extra‐temporal partial epilepsy" (Bernasconi et al., Annals of Neurology, 2001). See pdf at the end of the handbook (page 20).

    4. Cases presented in this document (page 15) should serve as didactic material only and not be used for other purposes. They should not be shared or published in any form.
