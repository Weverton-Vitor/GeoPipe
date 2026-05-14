from domain.repositories.filesystem_images_repository import (
    FileSystemImageRepository,
)


class ImageService:
    def __init__(self, image_repository: FileSystemImageRepository):
        self.image_repository = image_repository

    def get_images_for_month(self, run: str, year: str, month: str):
        images = self.image_repository.get_images(run=run, year=year, month=month)

        images = self._filter_images(images)
        images = self._sort_images(images)

        return images
    
    def get_images_for_day(self, run: str, year: str, month: str, day: str):
        images = self.image_repository.get_images(run=run, year=year, month=month, day=day)

        images = self._filter_images(images)
        images = self._sort_images(images)

        return images

    def _filter_images(self, images):
        return images

    def _sort_images(self, images):
        return sorted(images, key=lambda img: img.name)
