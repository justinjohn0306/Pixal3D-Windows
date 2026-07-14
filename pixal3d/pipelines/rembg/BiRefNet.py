from typing import *
import os
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms
from PIL import Image


class BiRefNet:
    def __init__(self, model_name: str = "ZhengPeng7/BiRefNet"):
        # REMBG_MODEL overrides the configured model, e.g. to avoid the
        # gated briaai/RMBG-2.0 repo when no HF login is available.
        model_name = os.environ.get("REMBG_MODEL", model_name)
        try:
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_name, trust_remote_code=True
            )
        except AttributeError:
            # Some BiRefNet/RMBG-2.0 mirrors ship older remote code whose bare
            # `Config` class predates transformers>=4.50 tie_weights(), which
            # calls config.get_text_config(). Shim it and retry.
            import sys
            import types
            for mod_name, mod in list(sys.modules.items()):
                if "transformers_modules" in mod_name and hasattr(mod, "Config"):
                    cfg_cls = getattr(mod, "Config")
                    if isinstance(cfg_cls, type) and not hasattr(cfg_cls, "get_text_config"):
                        cfg_cls.get_text_config = (
                            lambda self, decoder=False: types.SimpleNamespace(tie_word_embeddings=False)
                        )
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_name, trust_remote_code=True
            )
        self.model.eval()
        self.transform_image = transforms.Compose(
            [
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
    
    def to(self, device: str):
        self.model.to(device)

    def cuda(self):
        self.model.cuda()

    def cpu(self):
        self.model.cpu()
        
    def __call__(self, image: Image.Image) -> Image.Image:
        image_size = image.size
        input_images = self.transform_image(image).unsqueeze(0).to("cuda")
        # Prediction
        with torch.no_grad():
            preds = self.model(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(image_size)
        image.putalpha(mask)
        return image
    