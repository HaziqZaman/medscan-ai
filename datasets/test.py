from torchvision import datasets

dataset = datasets.ImageFolder(
    r"C:\Users\Aisha\Desktop\FINAL YEAR PROJECT\medscan-ai\dataset\IDC_regular_ps50_idx5"
)

print(dataset.classes)  # should show ['0', '1']
print(len(dataset))     # total number of images