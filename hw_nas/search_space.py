import random

OPS = ['3x3_conv', '5x5_conv', 'relu', 'add']

class NetworkBlock:
    def __init__(self, op_type, params):
        self.op_type = op_type # e.g. '3x3_conv'
        self.params = params # e.g. {'filter': 64}
    
    def __repr__(self):
        return f"Block({self.op_type}, {self.params})"

class Architecture:
    def __init__(self, blocks):
        self.blocks = blocks
    
    def __repr__(self):
        return " -> ".join([str(b) for b in self.blocks])

def get_random_architecture(max_depth=5):
    blocks = []
    for _ in range(random.randint(2, max_depth)):
        op = random.choice(OPS)
        params = {'filter': random.choice([32, 64, 128])}
        blocks.append(NetworkBlock(op, params))
    
    return Architecture(blocks)