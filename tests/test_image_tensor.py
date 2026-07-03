import io

import torch

from aholo_world_generate.util.image_tensor import first_image_tensor, tensor_to_png_bytes


def test_tensor_to_png_bytes_roundtrip():
    try:
        from PIL import Image
        import numpy  # noqa: F401
    except ImportError:
        return

    tensor = torch.zeros(2, 2, 3)
    tensor[0, 0] = torch.tensor([1.0, 0.0, 0.0])
    png = tensor_to_png_bytes(tensor)
    image = Image.open(io.BytesIO(png))
    assert image.size == (2, 2)
    assert image.mode == "RGB"


def test_first_image_tensor_batch():
    batch = torch.ones(1, 4, 4, 3) * 0.5
    first = first_image_tensor(batch)
    assert first is not None
    assert first.shape == (4, 4, 3)
