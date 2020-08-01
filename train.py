#!/user/bin/env python3

import torch
from pytorch_lightning import Trainer
from pytorch_lightning.core.lightning import LightningModule
from torch.nn import Linear, Sequential, LogSoftmax
from torch.nn import functional as F
from torch.utils.data import DataLoader
from torchvision import models
from torchvision import transforms
from torchvision.datasets import ImageFolder

root_dir = "../split-0"
num_classes = 8835


class LitModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.resnet = models.resnet50(
            pretrained=True,
            progress=True)
        self.resnet.fc = Sequential(
            Linear(in_features=2048, out_features=256, bias=True),
            Linear(in_features=256, out_features=num_classes, bias=True),
            LogSoftmax(dim=1))

    def forward(self, x):
        return self.resnet(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.resnet(x)
        loss = F.nll_loss(y_hat, y)
        tensorboard_logs = {'train_loss': loss}
        return {'loss': loss, 'log': tensorboard_logs}

    # def validation_epoch_end(self, val_step_outputs):
    #     x, y = val_step_outputs
    #     y_hat = self(x)
    #     loss = F.cross_entropy(y_hat, y)
    #     result = pl.EvalResult(checkpoint_on=loss)
    #     result.log('val_loss', loss)
    #     return result

    def configure_optimizers(self):
        return torch.optim.AdamW(self.parameters(), lr=1e-2)

    def train_dataloader(self):
        return DataLoader(
            dataset=ImageFolder(
                f"{root_dir}/train/",
                transform=transforms.Compose([
                    transforms.Resize(size=(224, 224)),
                    transforms.ToTensor()
                ])),
            batch_size=106,
            num_workers=8,
            shuffle=True)

    # def val_dataloader(self):
    #     return DataLoader(
    #         ImageFolder(
    #             f"{root_dir}/val/",
    #             transform=transforms.Compose([
    #                 transforms.Resize(size=(224, 224)),
    #                 transforms.ToTensor()
    #             ])),
    #         batch_size=64,
    #         num_workers=4,
    #         shuffle=False)


if __name__ == '__main__':
    model = LitModel()

    trainer = Trainer(
        gpus=1,
        auto_select_gpus=True,
        precision=16,
        early_stop_callback=True)

    trainer.fit(model)
