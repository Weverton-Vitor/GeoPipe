class Artifact:
    def __init__(
        self,
        name: str,
        artifact_type: str,
        stage: str,
        path: str,
    ):
        self.name = name
        self.type = artifact_type  # image, mask, metric
        self.stage = stage  # raw, fmask, water, clean
        self.path = path
