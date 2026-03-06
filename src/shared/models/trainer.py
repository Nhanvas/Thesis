# trainer.py
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger


class LightningModel(pl.LightningModule):
    """
    Lightning module wrapper.
    Modify training_step, validation_step, test_step for your task.
    """
    def __init__(self, model, loss_handler, metric_handler, optimizer_handler):
        super().__init__()
        self.model = model
        self.loss_handler = loss_handler
        self.metric_handler = metric_handler
        self.optimizer_handler = optimizer_handler
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        pred = self.model(x)
        
        loss = self.loss_handler(pred, y)
        acc = self.metric_handler.get_accuracy(pred, y)
        
        self.log("train_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log("train_acc", acc, prog_bar=True, on_step=False, on_epoch=True)
        
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        pred = self.model(x)
        
        loss = self.loss_handler(pred, y)
        acc = self.metric_handler.get_accuracy(pred, y)
        
        self.log("val_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log("val_acc", acc, prog_bar=True, on_step=False, on_epoch=True)
    
    def test_step(self, batch, batch_idx):
        x, y = batch
        pred = self.model(x)
        
        loss = self.loss_handler(pred, y)
        acc = self.metric_handler.get_accuracy(pred, y)
        
        self.log("test_loss", loss)
        self.log("test_acc", acc)
    
    def configure_optimizers(self):
        optimizer = self.optimizer_handler.get_optimizer(self.parameters())
        scheduler = self.optimizer_handler.get_scheduler(optimizer)
        
        if scheduler is None:
            return optimizer
        return {"optimizer": optimizer, "lr_scheduler": scheduler}


class Trainer:
    """
    Trainer wrapper.
    Modify callbacks and logger for your task.
    """
    def __init__(self, max_epochs=100, checkpoint_dir="./checkpoints/", experiment_dir=None):
        self.max_epochs = max_epochs
        self.checkpoint_dir = checkpoint_dir
        self.experiment_dir = experiment_dir
    
    def train(self, model, train_loader, val_loader, loss_handler, metric_handler, optimizer_handler):
        lightning_model = LightningModel(
            model=model,
            loss_handler=loss_handler,
            metric_handler=metric_handler,
            optimizer_handler=optimizer_handler
        )
        
        checkpoint_callback = ModelCheckpoint(
            dirpath=self.checkpoint_dir,
            filename="{epoch:02d}-{val_loss:.3f}",
            monitor="val_loss",
            mode="min",
            save_top_k=3,
            save_last=True
        )
        
        if self.experiment_dir:
            logger = CSVLogger(save_dir=self.experiment_dir, name="", version="")
        else:
            logger = CSVLogger(save_dir="./logs/", name="experiment")
        
        trainer = pl.Trainer(
            max_epochs=self.max_epochs,
            accelerator="auto",
            devices=1,
            callbacks=[checkpoint_callback],
            logger=logger
        )
        
        trainer.fit(lightning_model, train_loader, val_loader)
        
        return lightning_model
    
    def test(self, lightning_model, test_loader):
        trainer = pl.Trainer(accelerator="auto", devices=1)
        return trainer.test(lightning_model, test_loader)