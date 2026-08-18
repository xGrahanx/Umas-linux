import sys
sys.path.append('src')

from configs_loader import load_configs
from resources import ResourceRegistry
from states import State, Direction

load_configs("cafe")
print("Animations loaded:", len(ResourceRegistry.animations))
for k in ResourceRegistry.animations:
    print("  ", k)
