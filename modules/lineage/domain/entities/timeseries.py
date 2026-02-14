from datetime import date


class VolumeTimePoint:
    """
    Representa um ponto da série temporal de volume de água.
    """

    def __init__(self, date: date, volume: float):
        self.date = date
        self.volume = volume

    def __repr__(self):
        return f"VolumeTimePoint(date={self.date}, volume={self.volume})"


class VolumeTimeSeries:
    """
    Representa uma série temporal de volume de água.
    """

    def __init__(self, points: list[VolumeTimePoint]):
        self.points = points

    def sort(self):
        self.points.sort(key=lambda p: p.date)

    def filter_by_year(self, year: int):
        return VolumeTimeSeries([p for p in self.points if p.date.year == year])