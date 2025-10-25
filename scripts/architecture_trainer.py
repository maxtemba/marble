import sys
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import joblib
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

from hw_nas.search_space import get_random_architecture, build_pytorch_model
from hw_nas.predictor import featurize


# config paths
TIMING_PREDICTOR_PATH = "data/saved_models/timing_predictor.joblib"
POWER_PREDICTOR_PATH = "data/saved_models/power_predictor.joblib"

# test dataset (CIFAR-10) params
INPUT_CHANNELS = 3
INPUT_SIZE = 32
NUM_CLASSES = 10 # CIFAR-10 has 10 classes

# minimal Training Hyperparameters for demo
BATCH_SIZE = 64
LEARNING_RATE = 0.001
NUM_EPOCHS = 1 # ninimal epochs for demo
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# --- helper functions ---
def load_data():
    """Loads CIFAR-10 dataset."""
    print(f"Loading CIFAR-10 dataset (to ./data)...")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    
    train_set = torchvision.datasets.CIFAR10(root='./data', train=True,
                                             download=True, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=BATCH_SIZE,
                                               shuffle=True, num_workers=2)
    
    test_set = torchvision.datasets.CIFAR10(root='./data', train=False,
                                            download=True, transform=transform)
    test_loader = torch.utils.data.DataLoader(test_set, batch_size=BATCH_SIZE,
                                              shuffle=False, num_workers=2)
    print("Dataset loaded.")
    return train_loader, test_loader

def load_hardware_predictors(timing_path, power_path):
    """Loads the pre-trained hardware cost predictors."""
    timing_predictor = None
    power_predictor = None
    
    try:
        if os.path.exists(timing_path):
            timing_predictor = joblib.load(timing_path)
            print(f"Loaded timing predictor from {timing_path}")
        else:
            print(f"WARN: Timing predictor not found at {timing_path}")
            
        if os.path.exists(power_path):
            power_predictor = joblib.load(power_path)
            print(f"Loaded power predictor from {power_path}")
        else:
            print(f"WARN: Power predictor not found at {power_path}")
            
    except Exception as e:
        print(f"ERROR loading predictors: {e}")
        
    return timing_predictor, power_predictor

def train_model(model, train_loader, criterion, optimizer, num_epochs=1):
    """Minimal training loop."""
    print(f"Starting minimal training for {num_epochs} epoch(s) on {DEVICE}...")
    model.train() # set model to training mode
    for epoch in range(num_epochs):
        running_loss = 0.0
        for i, (inputs, labels) in enumerate(train_loader, 0):
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            if i % 100 == 99: # print every 100 mini-batches
                print(f'[Epoch {epoch + 1}, Batch {i + 1:5d}] loss: {running_loss / 100:.3f}')
                running_loss = 0.0
    print("Finished minimal training.")

def evaluate_accuracy(model, test_loader):
    """Calculates accuracy on the test set."""
    print("Evaluating accuracy on test set...")
    model.eval() # set model to evaluation mode
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
    accuracy = 100 * correct / total
    print(f"Accuracy: {accuracy:.2f} %")
    return accuracy

def evaluate_speed(model, num_runs=100):
    """Calculates average inference latency."""
    print(f"Evaluating inference speed (latency) on {DEVICE}...")
    model.eval()
    dummy_input = torch.randn(1, INPUT_CHANNELS, INPUT_SIZE, INPUT_SIZE).to(DEVICE)
    
    with torch.no_grad():
        _ = model(dummy_input)
        
    start_time = time.time()
    with torch.no_grad():
        for _ in range(num_runs):
            _ = model(dummy_input)
    end_time = time.time()
    
    avg_latency = (end_time - start_time) / num_runs * 1000 # in milliseconds
    print(f"Avg. Latency: {avg_latency:.4f} ms")
    return avg_latency

# --- main execution ---

def main():
    print("==============================================")
    print("--- HW-NAS Single Architecture Evaluator ---")
    print("==============================================")
    
    # 1. load Data and Hardware Predictors
    train_loader, test_loader = load_data()
    timing_predictor, power_predictor = load_hardware_predictors(
        TIMING_PREDICTOR_PATH, 
        POWER_PREDICTOR_PATH
    )
    
    # 2. generate a random architecture
    print("\n--- 1. Generating Architecture ---")
    arch = get_random_architecture(
        input_channels=INPUT_CHANNELS, 
        input_size=INPUT_SIZE
    )
    print(f"Generated Architecture:\n{arch}")
    
    # 3. build the PyTorch Model
    print("\n--- 2. Building PyTorch Model ---")
    model = build_pytorch_model(arch).to(DEVICE)
    print(model)
    
    # 4. train the Model (Minimally)
    print("\n--- 3. Training Model ---")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    train_model(model, train_loader, criterion, optimizer, num_epochs=NUM_EPOCHS)
    
    # 5. evaluate Metrics
    print("\n--- 4. Evaluating Metrics ---")
    
    # Metric A: Accuracy
    accuracy = evaluate_accuracy(model, test_loader)
    
    # Metric B: Speed (Latency)
    latency_ms = evaluate_speed(model)
    
    # Metric C: Predicted Hardware Cost
    print("Evaluating predicted hardware cost...")
    features = featurize(arch)
    features_2d = features.reshape(1, -1)
    
    predicted_wns = None
    predicted_power = None
    
    if timing_predictor:
        predicted_wns = timing_predictor.predict(features_2d)[0]
        print(f"Predicted Timing (WNS): {predicted_wns:.2f} ns")
    else:
        print("Skipping timing prediction (predictor not loaded).")
        
    if power_predictor:
        predicted_power = power_predictor.predict(features_2d)[0]
        print(f"Predicted Power: {predicted_power:.4f} W")
    else:
        print("Skipping power prediction (predictor not loaded).")

    # 6. final Summary
    print("\n==============================================")
    print("--- EVALUATION SUMMARY ---")
    print("==============================================")
    print(f"Architecture: {arch}")
    print("---")
    print(f"  Accuracy (Test Set): {accuracy:.2f} %")
    print(f"  Speed (Avg. Latency):  {latency_ms:.4f} ms")
    print("---")
    print(f"  Predicted WNS (Timing): {predicted_wns if predicted_wns is not None else 'N/A'} ns")
    print(f"  Predicted Power:        {predicted_power if predicted_power is not None else 'N/A'} W")
    print("==============================================")


if __name__ == "__main__":
    main()
