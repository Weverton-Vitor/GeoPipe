import utils.deepwatermap.inference as deep_water_map


def apply_deep_water_map(image_path: str, save_path: str, dependency):
    deep_water_map.main(image_path=image_path, save_path=save_path)
