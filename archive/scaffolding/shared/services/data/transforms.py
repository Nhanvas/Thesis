from typing import Tuple
from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """
    Base transformer class.
    Modify for your task.
    """
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class Transformer(BaseTransformer):
    """
    General transformer.
    Modify for your task.
    """
    def __init__(self, target_size: Tuple[int, int] = (224, 224), do_augmentation=False):
        self.target_size = target_size
        self.do_augmentation = do_augmentation

    def _augment(self, x):
        # Add augmentation here
        # Examples: flip, rotate, crop, etc.
        return x

    def _preprocess(self, x):
        # Add preprocessing here
        # Examples: resize, normalize, etc.
        return x

    def __call__(self, x):
        if self.do_augmentation:
            x = self._augment(x)
        
        x = self._preprocess(x)
        
        return x


# Segmentation example:
# class SegmentationTransformer(BaseTransformer):
#     def __init__(self, target_size=(224, 224), do_augmentation=False):
#         self.target_size = target_size
#         self.do_augmentation = do_augmentation
#
#     def _augment(self, image, mask):
#         # flip, rotate, etc.
#         return image, mask
#
#     def _preprocess(self, image, mask):
#         # resize, normalize, etc.
#         return image, mask
#
#     def __call__(self, image, mask):
#         if self.do_augmentation:
#             image, mask = self._augment(image, mask)
#         image, mask = self._preprocess(image, mask)
#         return {"image": image, "mask": mask}