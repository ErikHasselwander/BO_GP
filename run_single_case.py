from case_config import StarManager
from pathlib import Path


baseGeometryDict = [
      0.65, 0.4, 70, *([.25]*2), 0.1, *([.25]*4), 0.1, 0.95, 0.3, 0.8, 0.8, 3
]

a = StarManager()

a.runSingleCase("meshconv", baseGeometryDict, Path.cwd() / "meshconvstudy", Path.cwd() / "refFiles")