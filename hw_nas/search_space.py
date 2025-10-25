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

def get_random_architecture(max_depth=7, input_channels=3, input_size=32):
    """
    Generates a random, but VALID, architecture using a stateful process.
    """
    blocks = []
    
    # --- State tracking ---
    current_mode = 'conv' # 'conv' (2D) or 'linear' (1D)
    current_channels = input_channels
    current_size = input_size # Spatial dimension (e.g., 32x32)
    current_features = 0 # For linear layers
    
    for _ in range(random.randint(3, max_depth)):
        op = None
        
        if current_mode == 'conv':
            # --- We are in the 2D (conv) part of the network ---
            # Add 'flatten' as a possible op to transition to linear
            possible_ops = ['conv', 'relu', 'max_pool', 'global_avg_pool', 'flatten']
            op = random.choice(possible_ops)
            
            if op == 'conv':
                kernel_size = random.choice([3, 5])
                out_channels = random.choice([32, 64, 128])
                # NEW: Padding is now a searchable parameter
                padding = random.choice([0, 1, 'same']) 
                
                params = {
                    'in_channels': current_channels,
                    'out_channels': out_channels,
                    'kernel_size': kernel_size,
                    'padding': padding
                }
                blocks.append(NetworkBlock(op, params))
                
                # Update state
                current_channels = out_channels
                if padding == 'same':
                    pass # size is unchanged
                elif isinstance(padding, int):
                    current_size = (current_size - kernel_size + 2 * padding) + 1
                
            elif op == 'max_pool':
                kernel_size = 2
                params = {'kernel_size': kernel_size}
                blocks.append(NetworkBlock(op, params))
                
                # Update state
                current_size = math.floor(current_size / kernel_size)

            elif op == 'global_avg_pool':
                params = {}
                blocks.append(NetworkBlock(op, params))
                
                # Update state
                current_size = 1 # Global pool flattens spatial dim to 1x1
            
            elif op == 'relu':
                blocks.append(NetworkBlock('relu', {}))
                
            elif op == 'flatten':
                # --- Transition to linear mode ---
                in_features = current_channels * current_size * current_size
                params = {'in_features': in_features}
                blocks.append(NetworkBlock(op, params))
                
                # Update state
                current_mode = 'linear'
                current_features = in_features

        elif current_mode == 'linear':
            # --- We are in the 1D (linear) part of the network ---
            possible_ops = ['linear', 'relu']
            op = random.choice(possible_ops)

            if op == 'linear':
                out_features = random.choice([128, 256, 512])
                params = {
                    'in_features': current_features,
                    'out_features': out_features
                }
                blocks.append(NetworkBlock(op, params))
                
                # Update state
                current_features = out_features
                
            elif op == 'relu':
                blocks.append(NetworkBlock('relu', {}))

    # --- Final cleanup ---
    # Ensure the network has a final linear layer if it's in linear mode
    if current_mode == 'linear' and blocks[-1].op_type != 'linear':
        out_features = random.choice([128, 256, 512])
        params = {
            'in_features': current_features,
            'out_features': out_features
        }
        blocks.append(NetworkBlock('linear', params))

    # If we never flattened, add a final classifier
    elif current_mode == 'conv':
        # Flatten
        in_features = current_channels * current_size * current_size
        blocks.append(NetworkBlock('flatten', {'in_features': in_features}))
        # Linear
        out_features = random.choice([128, 256, 512])
        blocks.append(NetworkBlock('linear', {'in_features': in_features, 'out_features': out_features}))

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
                    padding=params['padding']
                ))
            elif op_type == 'relu':
                self.layers.append(nn.ReLU())
            elif op_type == 'max_pool':
                self.layers.append(nn.MaxPool2d(kernel_size=params['kernel_size']))
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