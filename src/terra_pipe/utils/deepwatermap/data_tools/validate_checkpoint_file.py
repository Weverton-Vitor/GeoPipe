import tensorflow as tf

ckpt = tf.train.load_checkpoint(
    "/media/weverton/D/Documentos/pibic/PIBIC_2024_2025/fmask-pipeline/src/utils/deepwatermap/checkpoints/cp.135.ckpt"
)
print(ckpt.get_variable_to_shape_map())
