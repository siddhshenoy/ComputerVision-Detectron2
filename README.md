# Installation
1. Open the .py file or .ipynb file and run the `pip install code`
2. Rename the folders according to your desired paths.

# Specifications
1. The dataset contains 3000 images along with their bounding boxes and instance segmentation images.
2. These images are broadly classified into 3 categories: **Ripe, Partially-Ripe and Unripe**
3. Detectron2 uses COCO JSON format for dataset which requires manual annotation. This is present in the `annotations_coco.json` and `annotations_coco_val.json` which are used for training and validation respectively.

# Working
1. The code will first install the detectron library along with any missing dependencies.
2. The code will then pick up the annotation files and create respective datasets
3. The model will then train on the 'strawberries' dataset.
