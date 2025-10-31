try:
    import numpy
    print('numpy available')
except ImportError:
    print('numpy not available')

try:
    import torch
    print('torch available')
except ImportError:
    print('torch not available')

try:
    import transformers
    print('transformers available')
except ImportError:
    print('transformers not available')

try:
    import sentence_transformers
    print('sentence_transformers available')
except ImportError:
    print('sentence_transformers not available')

try:
    import fastapi
    print('fastapi available')
except ImportError:
    print('fastapi not available')
