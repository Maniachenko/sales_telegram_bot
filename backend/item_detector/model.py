import torch.nn as nn
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor


# Define the backbone (ResNet50 with FPN)
def build_backbone():
    # Load a pre-trained resnet50 backbone, removing the fully connected layer (i.e., backbone part)
    backbone = torchvision.models.resnet50(pretrained=True)
    backbone = nn.Sequential(*list(backbone.children())[:-2])

    # Create a feature pyramid network (FPN) over the backbone
    backbone.out_channels = 2048  # Feature map channels
    return backbone


# Define the Faster R-CNN model
def build_faster_rcnn(num_classes, pretrained_backbone=True):
    # Create the backbone with a feature extractor (ResNet50 or others)
    backbone = build_backbone()

    # Create an anchor generator for the RPN, with different sizes and aspect ratios
    anchor_generator = AnchorGenerator(
        sizes=((32, 64, 128, 256, 512),),
        aspect_ratios=((0.5, 1.0, 2.0),) * len((32, 64, 128, 256, 512))
    )

    # Create RoI align (aligns feature map size with region proposals)
    roi_pooler = torchvision.ops.MultiScaleRoIAlign(
        featmap_names=['0'], output_size=7, sampling_ratio=2
    )

    # Create the Faster R-CNN model using the components above
    model = FasterRCNN(
        backbone,
        num_classes=num_classes,  # Number of classes (price tag + background)
        rpn_anchor_generator=anchor_generator,
        box_roi_pool=roi_pooler
    )

    return model


# Modify the final classifier head for your specific classes
def modify_head(model, num_classes):
    # Get the input features for the classifier head
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    # Replace the head of the model with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


# Complete model creation function
def get_model(num_classes):
    # Load a Faster R-CNN model pre-trained on COCO dataset
    model = build_faster_rcnn(num_classes)

    # Modify the head to suit the number of classes (2: price tag + background)
    model = modify_head(model, num_classes)

    return model


# Example Usage:
# num_classes should be 2 (one for price tag, one for background)
num_classes = 2
model = get_model(num_classes)

# Check the model architecture
print(model)
