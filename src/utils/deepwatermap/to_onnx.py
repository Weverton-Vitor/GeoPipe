import os
import tensorflow as tf
import tf2onnx
import onnx
import deepwatermap


def convert_to_onnx():
    # 1. Defina a PASTA onde os arquivos estão
    checkpoint_dir = (
        "/media/weverton/TOSHIBA EXT1/GeoPipe/src/utils/deepwatermap/checkpoints"
    )

    # 2. Defina o PREFIXO (o nome comum antes do .index)
    # IMPORTANTE: Não inclua a extensão .index ou .data aqui
    checkpoint_prefix = os.path.join(checkpoint_dir, "cp.135.ckpt")

    print(f"Buscando arquivos que começam com: {checkpoint_prefix}")

    # Validação simples antes de tentar carregar
    if not os.path.exists(checkpoint_prefix + ".index"):
        print(f"ERRO: Arquivo {checkpoint_prefix}.index não encontrado!")
        print(f"Arquivos na pasta: {os.listdir(checkpoint_dir)}")
        return

    # 3. Carregar Arquitetura
    model = deepwatermap.model()
    print("✓ Arquitetura do modelo carregada.")

    # 4. Carregar Pesos
    try:
        # No TF2/Keras, as vezes é necessário usar expect_partial() para checkpoints antigos
        model.load_weights(checkpoint_prefix).expect_partial()
        print("✓ Pesos carregados com sucesso!")
    except Exception as e:
        print(f"Falha ao carregar pesos: {e}")
        return

    # 5. Exportar para ONNX (Mesmo formato que seus modelos .h5)
    # (None, None, None, 6) -> Batch, Altura, Largura, Canais dinâmicos
    spec = (tf.TensorSpec((None, None, None, 6), tf.float32, name="input"),)

    print("Convertendo... aguarde.")
    model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=13)

    output_path = "deepwatermap_final.onnx"
    onnx.save(model_proto, output_path)
    print(f"Sucesso! Modelo salvo em: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    convert_to_onnx()
