import torch
import numpy as np
import torch.optim as optim
from torch import Tensor, nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
from torchvision import transforms
from torch.utils.data import DataLoader

from .dataloader import MVTEC
from .model import SpatialTransformerNetwork


train_transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize and crop the image to 224x224
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                  std=[0.229, 0.224, 0.225])
    
])

def start(data_dir ='../data/mvtec_anomaly_detection',batch_size = 32,learning_rate = 0.001,num_epochs = 10):
        
    mvtec_dataset = MVTEC(root_dir=data_dir, transform = train_transform)
    train_loader = DataLoader(mvtec_dataset, batch_size=batch_size, shuffle=True)


    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    stn_model = SpatialTransformerNetwork().to(device)
    criterion = nn.MSELoss()    
    optimizer = optim.Adam(stn_model.parameters(), lr=learning_rate)

    print("Training ..")
    
    for epoch in range(num_epochs):
        running_loss = 0.0
        for inputs, _ in train_loader:
            inputs = inputs.to(device)
            optimizer.zero_grad()
            outputs = stn_model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {running_loss / len(train_loader)}")

    print("Finished Training")
    return stn_model,train_loader


def visualize_stn(stn_model, data_loader):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    stn_model.to(device)
    stn_model.eval()

    with torch.no_grad():
        for inputs, _ in data_loader:
            inputs = inputs.to(device)
            print(inputs.size())

            # Get the STN-predicted image
            stn_predicted = stn_model(inputs)

            # Convert tensors to numpy arrays for visualization
            orig_image = inputs[0].cpu().numpy().transpose((1, 2, 0))
            stn_predicted_image = stn_predicted[0].cpu().numpy().transpose((1, 2, 0))

            # Undo normalization to display images correctly
            orig_image = (orig_image * [0.229, 0.224, 0.225]) + [0.485, 0.456, 0.406]
            orig_image = np.clip(orig_image, 0, 1)

            stn_predicted_image = (stn_predicted_image * [0.229, 0.224, 0.225]) + [0.485, 0.456, 0.406]
            stn_predicted_image = np.clip(stn_predicted_image, 0, 1)

            # Plot the images side by side
            fig, axes = plt.subplots(1, 2, figsize=(10, 5))
            axes[0].imshow(orig_image)
            axes[0].set_title('Original Image')
            axes[0].axis('off')

            axes[1].imshow(stn_predicted_image)
            axes[1].set_title('STN Predicted Image')
            axes[1].axis('off')

            plt.show()
            print(stn_predicted.size())
            print(len(stn_predicted_image))
            break  # Show only the first image from the batch

def save_model(model,model_name='../results/stn_model.pt'):
    torch.save(model.state_dict(), model_name)
    
def load_model(model,model_name='../results/stn_model.pt'):
    model = SpatialTransformerNetwork()
    model.load_state_dict(torch.load(model_name))
    model.eval()
    return model