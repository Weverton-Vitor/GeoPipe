from utils.deepwatermap import deepwatermap
import tensorflow as tf

model = deepwatermap.model()

checkpoint_path = "../checkpoints/cp.135.ckpt"
model.load_weights(checkpoint_path)
model.save("../checkpoints/model.keras")  # Formato recomendado
