import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, models
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import random

# -------------------------------
# Reproducibility
# -------------------------------
torch.manual_seed(42)
random.seed(42)

# -------------------------------
# Dataset path
# -------------------------------
DATASET_PATH = r"C:\Users\Aisha\Desktop\FINAL YEAR PROJECT\medscan-ai\dataset\IDC_regular_ps50_idx5"

# -------------------------------
# Image transformations
# -------------------------------
transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])

# -------------------------------
# Load dataset
# -------------------------------
dataset = datasets.ImageFolder(DATASET_PATH, transform=transform)

# -------------------------------
# Separate indices by class
# -------------------------------
class0_idx = []
class1_idx = []

for i, (_, label) in enumerate(dataset):
    if label == 0:
        class0_idx.append(i)
    else:
        class1_idx.append(i)

# -------------------------------
# Balanced sampling (30k each)
# -------------------------------
sample0 = random.sample(class0_idx, 30000)
sample1 = random.sample(class1_idx, 30000)

indices = sample0 + sample1
random.shuffle(indices)

subset = Subset(dataset, indices)

# -------------------------------
# Train / Val / Test split
# -------------------------------
train_size = int(0.8 * len(subset))
val_size = int(0.1 * len(subset))
test_size = len(subset) - train_size - val_size

train_set, val_set, test_set = torch.utils.data.random_split(
    subset, [train_size, val_size, test_size]
)

train_loader = DataLoader(train_set, batch_size=16, shuffle=True)
val_loader = DataLoader(val_set, batch_size=16)
test_loader = DataLoader(test_set, batch_size=16)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------------
# Load pretrained ResNet18
# -------------------------------
model = models.resnet18(weights="IMAGENET1K_V1")

# Freeze backbone for faster CPU training
for param in model.parameters():
    param.requires_grad = False

# Replace final layer
model.fc = nn.Linear(model.fc.in_features, 2)

model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.fc.parameters(), lr=0.0003)

epochs = 10

# -------------------------------
# Training
# -------------------------------
for epoch in range(epochs):

    model.train()
    train_loss = 0

    for images, labels in train_loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        train_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.4f}")

# -------------------------------
# Evaluation
# -------------------------------
model.eval()

all_preds = []
all_labels = []

with torch.no_grad():

    for images, labels in test_loader:

        images = images.to(device)

        outputs = model(images)

        preds = torch.argmax(outputs, dim=1).cpu().numpy()

        all_preds.extend(preds)
        all_labels.extend(labels.numpy())

accuracy = accuracy_score(all_labels, all_preds)

print("\nTEST RESULTS")
print("Accuracy:", accuracy)

print("\nClassification Report")
print(classification_report(all_labels, all_preds))

print("\nConfusion Matrix")
print(confusion_matrix(all_labels, all_preds))

# -------------------------------
# Save trained model
# -------------------------------
torch.save(model.state_dict(), "model_a/idc_model.pth")

print("\nModel saved to model_a/idc_model.pth")