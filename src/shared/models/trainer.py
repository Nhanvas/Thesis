import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger


class GAELightningModel(pl.LightningModule):
    """
    Lightning wrapper cho GAE unsupervised training.
    training_step: chỉ dùng interictal windows, không có labels.
    validation_step: compute reconstruction error trên val interictal.
    """
    def __init__(self, model, loss_handler, optimizer_handler):
        super().__init__()
        self.model = model
        self.loss_handler = loss_handler
        self.optimizer_handler = optimizer_handler
        self.val_scores = []  # thu thập scores để calibrate threshold

    def training_step(self, batch, batch_idx):
        x, edge_index, edge_weight, A = batch
        _, A_hat = self.model(x, edge_index, edge_weight)
        loss = self.loss_handler(A, A_hat)
        self.log("train_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, edge_index, edge_weight, A = batch
        _, A_hat = self.model(x, edge_index, edge_weight)
        loss = self.loss_handler(A, A_hat)
        score = self.model.anomaly_score(A, A_hat)
        self.val_scores.append(score)
        self.log("val_loss", loss, prog_bar=True, on_step=False, on_epoch=True)

    def on_validation_epoch_end(self):
        self.val_scores = []  # reset mỗi epoch

    def configure_optimizers(self):
        optimizer = self.optimizer_handler.get_optimizer(self.parameters())
        scheduler = self.optimizer_handler.get_scheduler(optimizer)
        if scheduler is None:
            return optimizer
        return {"optimizer": optimizer, "lr_scheduler": scheduler}


class Trainer:
    def __init__(self, max_epochs=100, checkpoint_dir="./checkpoints/", experiment_dir=None):
        self.max_epochs = max_epochs
        self.checkpoint_dir = checkpoint_dir
        self.experiment_dir = experiment_dir

    def train(self, model, train_loader, val_loader, loss_handler, optimizer_handler):
        lightning_model = GAELightningModel(
            model=model,
            loss_handler=loss_handler,
            optimizer_handler=optimizer_handler
        )

        checkpoint_callback = ModelCheckpoint(
            dirpath=self.checkpoint_dir,
            filename="{epoch:02d}-{val_loss:.4f}",
            monitor="val_loss",
            mode="min",
            save_top_k=3,
            save_last=True
        )

        logger = CSVLogger(
            save_dir=self.experiment_dir or "./logs/",
            name="", version=""
        )

        trainer = pl.Trainer(
            max_epochs=self.max_epochs,
            accelerator="auto",
            devices=1,
            callbacks=[checkpoint_callback],
            logger=logger,
            deterministic=True  # reproducibility, seed=42
        )

        trainer.fit(lightning_model, train_loader, val_loader)
        return lightning_model

    def test(self, lightning_model, test_loader):
        trainer = pl.Trainer(accelerator="auto", devices=1)
        return trainer.test(lightning_model, test_loader)