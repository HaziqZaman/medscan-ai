import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Load model once
model = models.resnet18(pretrained=False)
model.fc = nn.Linear(model.fc.in_features, 2)

model.load_state_dict(torch.load("ml/model_a/idc_model.pth", map_location="cpu"))
model.eval()

# Transform (IMPORTANT: same as training)
transform = transforms.Compose([
    transforms.Resize((50, 50)),
    transforms.ToTensor()
])


def predict_idc(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(image)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, 1)

    label = "IDC" if predicted.item() == 1 else "Non-IDC"

    return label, float(confidence.item())