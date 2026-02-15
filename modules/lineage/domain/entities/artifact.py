class Artifact:
    def __init__(
        self,
        name: str,
        value: float,
    ):
        self.name = name
        self.value = value

class ArtifactImage(Artifact):
    def __init__(
        self,
        name: str,
        path: str,
        image_type: str,
    ):
        super().__init__(name, 0.0)  # Call parent constructor with default value
        self.path = path
        self.image_type = image_type
