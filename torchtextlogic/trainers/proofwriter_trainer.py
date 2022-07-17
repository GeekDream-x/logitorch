from typing import Dict, Tuple

import pytorch_lightning as pl
import torch
import torch.nn as nn
from transformers import Adafactor
from transformers.modeling_outputs import SequenceClassifierOutput

from torchtextlogic.models.proofwriter import ProofWriter


class ProofWriterTrainer(pl.LightningModule):
    def __init__(
        self, pretrained_model: str = "t5-large", learning_rate: float = None
    ) -> None:
        super().__init__()
        self.model = ProofWriter(pretrained_model)
        self.learning_rate = learning_rate

    def forward(self, x, y) -> SequenceClassifierOutput:  # type: ignore
        return self.model(x, y)

    def configure_optimizers(self):
        return Adafactor(
            self.model.parameters(),
            relative_step=True,
            warmup_init=True,
            lr=self.learning_rate,
        )

    def training_step(self, train_batch: Tuple[Dict[str, torch.Tensor], torch.Tensor], batch_idx: int) -> torch.Tensor:  # type: ignore
        x, y = train_batch
        loss = self(x, y).loss
        self.log("train_loss", loss, on_epoch=True)
        return loss

    def validation_step(self, val_batch: Tuple[Dict[str, torch.Tensor], torch.Tensor], batch_idx: int) -> None:  # type: ignore
        x, y = val_batch
        loss = self(x, y).loss
        self.log("val_loss", loss, on_epoch=True)
