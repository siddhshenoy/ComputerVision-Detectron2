# -*- coding: utf-8 -*-
"""Detectron (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11PbFcOIvYPfiZM30XL7C3i51qZ7Su1e7
"""

#Optional, change the paths below if you are not running from drive!
from google.colab import drive
drive.mount('/content/drive')

"""# Install detectron2"""

!python -m pip install pyyaml==5.1
import sys, os, distutils.core
# Note: This is a faster way to install detectron2 in Colab, but it does not include all functionalities.
# See https://detectron2.readthedocs.io/tutorials/install.html for full installation instructions
!git clone 'https://github.com/facebookresearch/detectron2'
dist = distutils.core.run_setup("./detectron2/setup.py")
!python -m pip install {' '.join([f"'{x}'" for x in dist.install_requires])}
sys.path.insert(0, os.path.abspath('./detectron2'))

# Properly install detectron2. (Please do not install twice in both ways)
# !python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

sys.path.insert(0, os.path.abspath('./detectron2'))
import torch, detectron2
!nvcc --version
TORCH_VERSION = ".".join(torch.__version__.split(".")[:2])
CUDA_VERSION = torch.__version__.split("+")[-1]
print("torch: ", TORCH_VERSION, "; cuda: ", CUDA_VERSION)
print("detectron2:", detectron2.__version__)

# Some basic setup:
# Setup detectron2 logger
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import numpy as np
import os, json, cv2, random
from google.colab.patches import cv2_imshow

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog

"""# Train on a custom dataset

In this section, we show how to train an existing detectron2 model on a custom dataset in a new format.

We use [the balloon segmentation dataset](https://github.com/matterport/Mask_RCNN/tree/master/samples/balloon)
which only has one class: balloon.
We'll train a balloon segmentation model from an existing model pre-trained on COCO dataset, available in detectron2's model zoo.

Note that COCO dataset does not have the "balloon" category. We'll be able to recognize this new class in a few minutes.

## Prepare the dataset
"""

from detectron2.data.datasets import register_coco_instances

dir = '/content/drive/MyDrive/ComputerVision-Detectron/'

register_coco_instances("strawberries", {}, 
                        f"{dir}annotations_coco.json", 
                        f"{dir}images") #TRAIN


fruits_nuts_metadata = MetadataCatalog.get("strawberries")
dataset_dicts = DatasetCatalog.get("strawberries")

register_coco_instances("strawberries_val", {}, 
                        f"{dir}annotations_coco_val.json", 
                        f"{dir}images") # VALIDATION

"""## Train!

Now, let's fine-tune a COCO-pretrained R50-FPN Mask R-CNN model on the balloon dataset. It takes ~2 minutes to train 300 iterations on a P100 GPU.

"""

from detectron2.engine import DefaultTrainer

cfg = get_cfg()
cfg.merge_from_file('./detectron2/configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml')
#cfg.merge_from_file('./detectron2/configs/COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml')
cfg.DATASETS.TRAIN = ("strawberries",)
cfg.DATASETS.TEST = ("strawberries_val",)
cfg.DATALOADER.NUM_WORKERS = 2
cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x/137849600/model_final_f10217.pkl"  # Let training initialize from model zoo
cfg.SOLVER.IMS_PER_BATCH = 2  # This is the real "batch size" commonly known to deep learning people
cfg.SOLVER.BASE_LR = 0.025  # pick a good LR
cfg.SOLVER.MAX_ITER = 100    # 300 iterations seems good enough for this toy dataset; you will need to train longer for a practical dataset
cfg.SOLVER.STEPS = []        # do not decay learning rate
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # The "RoIHead batch size". 128 is faster, and good enough for this toy dataset (default: 512)
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3  # only has one class (ballon). (see https://detectron2.readthedocs.io/tutorials/datasets.html#update-the-config-for-new-datasets)
# NOTE: this config means the number of classes, but a few popular unofficial tutorials incorrect uses num_classes+1 here.
cfg.CUDA_LAUNCH_BLOCKING=1


os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg) 
trainer.resume_or_load(resume=False)
trainer.train()

from detectron2.utils.visualizer import ColorMode

import random
cfg.MODEL.WEIGHTS = os.path.join("/content/drive/MyDrive/ComputerVision-Detectron/", "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5   # set the testing threshold for this model
cfg.DATASETS.TEST = ("strawberries_val", )
predictor = DefaultPredictor(cfg)
dataset_dicts = DatasetCatalog.get("strawberries_val")
fruits_nuts_metadata = MetadataCatalog.get("strawberries_val")

# SAMPLES EXTRACTED FROM VALIDATION
for d in random.sample(dataset_dicts, 10):    

    im = cv2.imread(d["file_name"])

    outputs = predictor(im)

    v = Visualizer(im[:, :, ::-1],

                   metadata=fruits_nuts_metadata,

                   scale=0.8,

                   instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels

    )

    v = v.draw_instance_predictions(outputs["instances"].to("cpu"))

    cv2_imshow(v.get_image()[:, :, ::-1])

#PREDICTING ON GIVEN TEST IMAGES

import time
images = ["1002", "1029", "1099", "1104","1112"]
t = time.time()
predictor = DefaultPredictor(cfg)
for image_name in images:
  im = cv2.imread(f"/content/drive/MyDrive/ComputerVision-Detectron/validation/images/{image_name}.png")
  outputs = predictor(im)
  cv2_imshow(im)
  v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1.2)
  out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
  cv2_imshow(out.get_image()[:, :, ::-1])
etime = time.time()
print("diff: {}".format(etime - t))

# Commented out IPython magic to ensure Python compatibility.
# Look at training curves in tensorboard:
# %load_ext tensorboard
# %tensorboard --logdir output

"""## Inference & evaluation using the trained model

"""

# Inference should use the config with parameters that are used in training
# cfg now already contains everything we've set previously. We changed it a little bit for inference:
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")  # path to the model we just trained
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7   # set a custom testing threshold
predictor = DefaultPredictor(cfg)

"""Then, we randomly select several samples to visualize the prediction results."""

from detectron2.utils.visualizer import ColorMode

for d in random.sample(dataset_dicts, 10):    
    im = cv2.imread(d["file_name"])
    outputs = predictor(im)  # format is documented at https://detectron2.readthedocs.io/tutorials/models.html#model-output-format
    v = Visualizer(im[:, :, ::-1],
                   metadata=fruits_nuts_metadata, 
                   scale=0.5, 
                   instance_mode=ColorMode.IMAGE   # remove the colors of unsegmented pixels. This option is only available for segmentation models
    )
    out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
    cv2_imshow(out.get_image()[:, :, ::-1])

"""We can also evaluate its performance using AP metric implemented in COCO API.
This gives an AP of ~70. Not bad!
"""

from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
evaluator = COCOEvaluator("strawberries", output_dir="./output")
val_loader = build_detection_test_loader(cfg, "strawberries")
print(inference_on_dataset(predictor.model, val_loader, evaluator))
# another equivalent way to evaluate the model is to use `trainer.test`