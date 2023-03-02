## Installation and use of ITK-SNAP (all platforms)

![](../assets/media/image40.png)

ITK-SNAP is a visualization software available on major platforms (Windows, macOS and Linux).

Download here: <http://www.itksnap.org/pmwiki/pmwiki.php?n=Downloads.SNAP3>

Select the latest version corresponding to your platform.


### Load and view MR images

When first opening ITK-SNAP, you will be presented with the following
screen.

![](../assets/media/image41.png)

To open the first image, select "File \> Open Main Image".

![](../assets/media/image42.png)

The dialog box "Open Image -- ITK-SNAP" will open. Click on "Browse" to
search for the file you want to load (load the T1-weighted image at this
stage).

![](../assets/media/image43.png)

Once you click "Open", the following dialog box will appear:

![](../assets/media/image44.png)

Click "Next". The image will be loaded, and a final dialog box with the
image characteristics will be displayed. Click on "Finish".

![](../assets/media/image45.png)

ITK-SNAP allows juxtaposition of multiple images. To add a new image,
select "File \> Add Another Image ...".

![](../assets/media/image46.png)

The same dialog box presented earlier will appear. We recommend loading
the T2-weighted file. Until the selection of the image, the procedure is
exactly the same.

![](../assets/media/image47.png)

When clicking "Next", ITK-SNAP will ask to display the additional image
as a separate image, or as an overlay. Choose "As a separate image
(shown beside other images)". Click "Next", and a dialog box summarizing
the additional image's properties will appear. Click on "Finish" to
proceed.

![](../assets/media/image48.png)

Notice that both images are **not** juxtaposed next to one another.

To enable this display, click the button highlighted in red as follows.

![](../assets/media/image49.png)

![](../assets/media/image50.png)

To explore one orientation more closely, you can extend its view to full
screen by clicking one of the highlighted red buttons.

![](../assets/media/image51.png)

This will result in the following display (when axial view is selected).

![](../assets/media/image52.png)

Re-click the same button to revert to the original view.

Repeat the procedure of adding additional images for *relative
intensity* and *gradient*.

![](../assets/media/image53.png)


### Adjusting image color and contrast

Select "Tools \> Image Contrast/Contrast Adjustment...".

![](../assets/media/image54.png)

The following dialog box will appear:

![](../assets/media/image55.png)

First, select the "*Color Map*" panel. Then, select *relative intensity*
in the left panel.

![](../assets/media/image56.png)

Next, click on "Select a colormap" and select "Hot".

![](../assets/media/image57.png)

Repeat this for the gradient image. The viewer should now be organized
as illustrated below.

![](../assets/media/image58.png)

Next, access the "Contrast" Panel. To adjust the contrast of the
*relative intensity* image, you can slide the point (solid yellow dot)
situated on the left of the intensity histogram to the right.

![](../assets/media/image59.png)

Conversely, slide the point on the right of the intensity histogram
towards the left to adjust the gradient contrast.

![](../assets/media/image60.png)

Your images are now ready to be reviewed.

!!! info "Important points when evaluating a case"

    The textures pipeline should be used only when a FCD Type II is suspected. It is NOT recommended to use this pipeline for the detection of any other epileptogenic lesions, such as hippocampal sclerosis, heterotopias or tumors.

    The output images of the pipeline include:
    1) T1
    2) FLAIR
    3) gradient magnitude map (*modeling blurring: darker regions compared to the surroundings*), and
    4) relative intensity map (*showing the hyperintensity of the FCD relative to the rest of the brain GM and WM*)
    
    Maps do not show only changes related to the FCD. The relative
    intensity maps display hyperintensities in other brain
    regions (including the central areas, insula, mesiotemporal lobe, the
    basal ganglia and thalamus), due to biological reasons other than the
    presence of an FCD. Detection of an FCD in these areas are more difficult.

    On the gradient magnitude map, the contour of the
    ventricles appears as a bright signal because of the strong contrast
    between WM and CSF.

    FCD Type II lesions are typically characterized by the **co-occurrence
    of blurring (dark cortex on gradient map) and hyperintensities (on
    relative intensity map)**.

    **In general, any lesion highlighted on texture maps should be visible
    on conventional T1 and FLAIR images.**

