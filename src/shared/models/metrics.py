from torchmetrics.functional import accuracy, precision, recall, f1_score, jaccard_index

class MetricHandler:
    """
    Metric handler.
    Modify this for your task.
    """
    def __init__(self, task="multiclass", num_classes=2, threshold=0.5, smooth=1e-5):
        self.task = task
        self.num_classes = num_classes
        self.threshold = threshold
        self.smooth = smooth
    
    # Classification
    def get_accuracy(self, pred, target):
        return accuracy(pred, target, task=self.task, num_classes=self.num_classes)
    
    def get_precision(self, pred, target):
        return precision(pred, target, task=self.task, num_classes=self.num_classes, average="macro")
    
    def get_recall(self, pred, target):
        return recall(pred, target, task=self.task, num_classes=self.num_classes, average="macro")
    
    def get_f1(self, pred, target):
        return f1_score(pred, target, task=self.task, num_classes=self.num_classes, average="macro")
    
    # Segmentation
    def get_iou(self, pred, target):
        return jaccard_index(pred, target, task="binary", threshold=self.threshold)
    
    def get_dice(self, pred, target):
        intersection = (pred * target).sum()
        return (2. * intersection + self.smooth) / (pred.sum() + target.sum() + self.smooth)