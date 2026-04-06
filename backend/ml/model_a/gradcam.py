import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import models, transforms


# --- Load Model ---
model = models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load("ml/model_a/idc_model.pth", map_location="cpu"))
model.eval()


# --- Transform ---
transform = transforms.Compose([
    transforms.Resize((50, 50)),
    transforms.ToTensor()
])


def generate_gradcam(image_path):
    image = Image.open(image_path).convert("RGB")
    input_tensor = transform(image).unsqueeze(0)

    gradients = []
    activations = []

    def forward_hook(module, inp, output):
        activations.append(output)

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])

    target_layer = model.layer4[1].conv2

    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)

    # Forward pass
    output = model(input_tensor)
    pred_class = output.argmax(dim=1).item()

    # Backward pass
    model.zero_grad()
    output[0, pred_class].backward()

    # Remove hooks
    forward_handle.remove()
    backward_handle.remove()

    grads = gradients[0].detach().cpu().numpy()[0]
    acts = activations[0].detach().cpu().numpy()[0]

    # Channel weights
    weights = np.mean(grads, axis=(1, 2))

    # Weighted sum
    cam = np.zeros(acts.shape[1:], dtype=np.float32)
    for i, w in enumerate(weights):
        cam += w * acts[i]

    # ReLU
    cam = np.maximum(cam, 0)

    # Resize
    cam = cv2.resize(cam, (50, 50), interpolation=cv2.INTER_CUBIC)

    # Normalize
    cam = cam - cam.min()
    cam = cam / (cam.max() + 1e-8)

    # Convert to uint8
    cam_uint8 = np.uint8(255 * cam)

    # Smooth
    cam_uint8 = cv2.GaussianBlur(cam_uint8, (5, 5), 0)

    # Original image
    original = np.array(image.resize((50, 50)))
    original = cv2.cvtColor(original, cv2.COLOR_RGB2BGR)

    # Raw heatmap
    heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)

    # Overlay image
    overlay = cv2.addWeighted(original, 0.82, heatmap, 0.18, 0)

    # Threshold strongest activation area
    _, thresh = cv2.threshold(cam_uint8, 210, 255, cv2.THRESH_BINARY)

    # Clean mask
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours on overlay only
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 12:
            epsilon = 0.03 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            cv2.drawContours(overlay, [approx], -1, (0, 255, 0), 1)

    # Strongest point on overlay only
    _, _, _, max_loc = cv2.minMaxLoc(cam_uint8)
    cv2.circle(overlay, max_loc, 3, (255, 255, 255), -1)
    cv2.circle(overlay, max_loc, 5, (0, 0, 0), 1)

    return {
        "heatmap": heatmap,
        "overlay": overlay
    }