from case_config import StarManager
from pathlib import Path


baseGeometryDict = [
      0.65, 0.4, 70, *([.25]*2), 0.075, *([.25]*4), 0.075, 1.1, 0.3, 1, 0.85, 3
]

a = StarManager()

a.runSingleCase("case", baseGeometryDict, Path.cwd() / "cases", Path.cwd() / "refFiles")