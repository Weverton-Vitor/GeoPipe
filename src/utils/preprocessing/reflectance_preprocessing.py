import ee


def scale_offset_image(image: ee.Image, scale_factor: float | int, offset: float | int):
    """Aplica a transformação de escala e deslocamento a uma única imagem

    Args:
        image (ee.Image): Imagem que será processada
        scale_factor (float | int): Fator de escala
        offset (float | int): Fator de deslocamento

    Returns:
        ee.Image: Imagem transformada
    """

    return (
        image.multiply(scale_factor)
        .add(offset)
        .copyProperties(image, image.propertyNames())
    )
