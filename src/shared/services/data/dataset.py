from torch.utils.data import Dataset
from typing import Optional
from .transforms import BaseTransformer


class BaseDataset(Dataset):
    """
    Base dataset class.
    Modify for your task.
    """
    def __init__(self, data_dir: str, transform: Optional[BaseTransformer] = None):
        self.data_dir = data_dir
        self.transform = transform
        self.samples = []  # Load your data here
        self.labels = []
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        # Classification (default)
        x = self.samples[idx]
        y = self.labels[idx]
        
        if self.transform:
            x = self.transform(x)
        
        return x, y
        
        # Segmentation:
        # image = self.samples[idx]
        # mask = self.masks[idx]
        # if self.transform:
        #     sample = self.transform(image, mask)
        #     image, mask = sample["image"], sample["mask"]
        # return image, mask