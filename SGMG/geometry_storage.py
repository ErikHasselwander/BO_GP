from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Curve:
    points: np.ndarray
    face_name: str

    def length(self):
        return len(self.points)


@dataclass
class Sketch:
    name: str
    curves: list[Curve] = field(default_factory=list)

    def add_curve(self, curve: Curve):
        if not isinstance(curve.points, np.ndarray) or curve.points.shape[1] != 2:
            raise TypeError("Curve must be a numpy array of shape (N, 2).")
        self.curves.append(curve)

    def length(self):
        return len(self.curves)


@dataclass
class GeometryStorage:
    name: str
    sketches: dict[str, Sketch] = field(default_factory=dict)

    def add_sketch(self, sketch: Sketch):
        if sketch.name in self.sketches:
            raise ValueError(f"Sketch '{sketch.name}' already exists.")
        self.sketches[sketch.name] = sketch

    def add_curve(self, sketch_name: str, curve: Curve):
        if sketch_name not in self.sketches:
            raise ValueError(
                f"Sketch '{sketch_name}' does not exist. Add the sketch first."
            )
        self.sketches[sketch_name].add_curve(curve)

    def get_sketches(self) -> dict[str, Sketch]:
        return self.sketches

    def plot_geometry(self):
        fig, ax = plt.subplots()

        for sketch in self.sketches.values():
            for curve in sketch.curves:
                points = curve.points
                if len(points) == 2:
                    midpoint = (points[0] + points[1]) / 2
                    points = np.vstack([points[0], midpoint, points[1]])

                curve_mid_idx = int(np.floor(len(points) / 2))
                ax.plot(points[:, 0], points[:, 1], label=curve.face_name)
                ax.annotate(
                    f"${curve.face_name}$",
                    (points[curve_mid_idx, 0], points[curve_mid_idx, 1]),
                )

        ax.set_ylim(bottom=0)
        return fig, ax
