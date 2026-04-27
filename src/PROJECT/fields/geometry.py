from __future__ import annotations

from math import isclose


type Coordinate = tuple[float, float]


def normalize_polygon(points: list[Coordinate] | tuple[Coordinate, ...]) -> tuple[Coordinate, ...]:
    if len(points) < 3:
        raise ValueError("polygon 은 최소 3개 좌표가 필요합니다.")
    normalized = tuple((float(lat), float(lng)) for lat, lng in points)
    distinct = {(lat, lng) for lat, lng in normalized}
    if len(distinct) < 3:
        raise ValueError("polygon 은 서로 다른 좌표가 최소 3개 필요합니다.")
    if normalized[0] != normalized[-1]:
        normalized = normalized + (normalized[0],)
    return normalized


def bounding_box(points: tuple[Coordinate, ...]) -> dict[str, float]:
    latitudes = [lat for lat, _ in points]
    longitudes = [lng for _, lng in points]
    return {
        "min_latitude": min(latitudes),
        "max_latitude": max(latitudes),
        "min_longitude": min(longitudes),
        "max_longitude": max(longitudes),
    }


def centroid(points: tuple[Coordinate, ...]) -> Coordinate:
    if len(points) < 4:
        raise ValueError("닫힌 polygon 좌표가 필요합니다.")
    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index in range(len(points) - 1):
        y0, x0 = points[index]
        y1, x1 = points[index + 1]
        cross = (x0 * y1) - (x1 * y0)
        area_twice += cross
        centroid_x += (x0 + x1) * cross
        centroid_y += (y0 + y1) * cross

    if isclose(area_twice, 0.0, abs_tol=1e-12):
        avg_lat = sum(lat for lat, _ in points[:-1]) / (len(points) - 1)
        avg_lng = sum(lng for _, lng in points[:-1]) / (len(points) - 1)
        return (avg_lat, avg_lng)

    area_factor = area_twice * 3.0
    return (centroid_y / area_factor, centroid_x / area_factor)


def point_in_polygon(latitude: float, longitude: float, polygon: tuple[Coordinate, ...]) -> bool:
    inside = False
    x = longitude
    y = latitude
    for index in range(len(polygon) - 1):
        y0, x0 = polygon[index]
        y1, x1 = polygon[index + 1]
        intersects = ((y0 > y) != (y1 > y)) and (
            x < ((x1 - x0) * (y - y0) / ((y1 - y0) or 1e-12)) + x0
        )
        if intersects:
            inside = not inside
    return inside
