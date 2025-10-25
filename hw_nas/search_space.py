import random
import torch
import torch.nn as nn
import math

# --- Generic OPS list ---
# 'add' has been removed.
# We use generic names; the parameters will be in the block.
OPS = [
    'conv',
    'relu',
    'max_pool',
    'global_avg_pool',
    'linear',
]

class NetworkBlock:
    def __init__(self, op_type, params):
        self.op_type = op_type # e.g. 'conv', 'relu', 'linear'
        self.params = params # e.g. {'in_channels': 3, 'out_channels': 32, 'kernel_size': 3, 'padding': 1}
    
    def __repr__(self):
        return f"Block({self.op_type}, {self.params})"

class Architecture:
    def __init__(self, blocks):
        self.blocks = blocks
    
    def __repr__(self):
        return " -> ".join([str(b) for b in self.blocks])

def get_random_architecture(max_depth=8, input_channels=3, input_size=32):
    """
    Generates a random, VALID, and *meaningful* architecture using a
    stage-based process (Stem -> Head -> Classifier).
    """
    blocks = []
    
    # --- State tracking ---
    current_channels = input_channels
    current_size = input_size # Spatial dimension (e.g., 32x32)
    current_features = 0 # For linear layers

    # --- Phase 1: Stem (Convolutional Body) ---
    # We'll reserve 3-4 layers for the head and classifier
    num_conv_layers = random.randint(2, max_depth - 3)
    
    for _ in range(num_conv_layers):
        # In the stem, we only choose between Conv, ReLU, and MaxPool
        # We make 'conv' more likely to be chosen
        possible_ops = ['conv', 'conv', 'relu', 'max_pool']
        op = random.choice(possible_ops)
        
        # --- Add conv block ---
        if op == 'conv':
            kernel_size = random.choice([3, 5])
            # Ensure channels generally increase or stay the same
            out_channels = random.choice([current_channels, current_channels * 2, current_channels * 4])
            # Cap the number of channels
            out_channels = min(out_channels, 128) 
            
            stride = random.choice([1, 2])
            
            # Don't stride if the image is already small
            if current_size <= 4 and stride == 2:
                stride = 1
                
            if stride == 1:
                padding = 'same'
                padding_int = kernel_size // 2
            else:
                padding = kernel_size // 2
                padding_int = padding
                
            params = {
                'in_channels': current_channels,
                'out_channels': out_channels,
                'kernel_size': kernel_size,
                'padding': padding,
                'stride': stride
            }
            blocks.append(NetworkBlock(op, params))
            
            # Update state
            current_channels = out_channels
            if padding == 'same':
                current_size = math.ceil(current_size / stride)
            else:
                current_size = math.floor((current_size - kernel_size + 2 * padding_int) / stride) + 1

        # --- Add relu ---
        elif op == 'relu':
            # Avoid useless, back-to-back ReLUs
            if not blocks or blocks[-1].op_type == 'relu':
                continue
            blocks.append(NetworkBlock('relu', {}))

        # --- Add pool ---
        elif op == 'max_pool':
            # Don't pool if image is too small
            if current_size <= 4:
                continue
                
            kernel_size = 2
            stride = 2
            params = {
                'kernel_size': kernel_size,
                'stride': stride
            }
            blocks.append(NetworkBlock(op, params))
            
            # Update state
            current_size = math.floor((current_size - kernel_size) / stride) + 1

    # --- Phase 2: Transition Head ---
    # This is now an explicit, non-random step
    
    # 1. Global Average Pool
    blocks.append(NetworkBlock('global_avg_pool', {}))
    current_size = 1
    
    # 2. Flatten
    in_features = current_channels * current_size * current_size
    params = {'in_features': in_features}
    blocks.append(NetworkBlock('flatten', params))
    current_features = in_features

    # --- Phase 3: Classifier (Linear Layers) ---
    # Generate 1 or 2 linear layers
    num_linear_layers = random.randint(1, 2)
    
    for i in range(num_linear_layers):
        # Add ReLU *before* the linear layer (as an activation)
        # But not before the very first linear layer
        if i > 0:
            blocks.append(NetworkBlock('relu', {}))
            
        out_features = random.choice([128, 256, 512])
        # Ensure last layer is smaller
        if i == num_linear_layers - 1:
             out_features = 128
             
        params = {
            'in_features': current_features,
            'out_features': out_features
        }
        blocks.append(NetworkBlock('linear', params))
        
        # Update state
        current_features = out_features

    return Architecture(blocks)


# ----------------------------------------------------------------------
# --- NEW: PyTorch Translator (Simpler & More Flexible) ---
# ----------------------------------------------------------------------

class TranslatedPytorchModel(nn.Module):
    """
    Builds a PyTorch model from a VALID Architecture object.
    """
    def __init__(self, arch: Architecture):
        super().__init__()
        self.layers = nn.ModuleList()
        self.arch = arch

        for block in arch.blocks:
            op_type = block.op_type
            params = block.params
            
            if op_type == 'conv':
                # Parameters are read directly from the block
                self.layers.append(nn.Conv2d(
                    in_channels=params['in_channels'],
                    out_channels=params['out_channels'],
                    kernel_size=params['kernel_size'],
                    padding=params['padding'],
                    stride=params['stride']
                ))
            elif op_type == 'relu':
                self.layers.append(nn.ReLU())
            elif op_type == 'max_pool':
                self.layers.append(nn.MaxPool2d(
                    kernel_size=params['kernel_size'],
                    stride=params['stride']
                ))
            elif op_type == 'global_avg_pool':
                self.layers.append(nn.AdaptiveAvgPool2d((1, 1)))
            elif op_type == 'flatten':
                self.layers.append(nn.Flatten())
            elif op_type == 'linear':
                self.layers.append(nn.Linear(
                    in_features=params['in_features'],
                    out_features=params['out_features']
                ))
                
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

def build_pytorch_model(arch: Architecture):
    """
    Public helper function to create a PyTorch model from an Architecture.
    """
    return TranslatedPytorchModel(arch)

