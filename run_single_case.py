from case_config import StarManager
from pathlib import Path


# C_ är fri punkt
# C2_ är "punkt mellan dom två som finns"
baseGeometryDict = [
      # 0.65, 0.4, 70, 0.05, 0.05, 0.11, *([.25]*4), 0.11, 1.25, .4, 1.1, 0.8, 3 # C_1
      # 0.65, 0.4, 70,   0.9, 0.9, 0.05, *([.25]*4), 0.07, 1, .47, .95-.065, 0.7, 3 # C_2
      # 0.65, 0.4, 60,   0.9, 0.9, 0.05, *([.25]*4), 0.07, 0.8, 0.6, 0, 0, 3 # C2_1
      0.65, 0.4, 15,   0.9, 0.9, 0.05, *([.25]*4), 0.07, 0.8, 0.6, 3 # C2_1
]

# top: 2 3 11 12
# bottom: 1 8 9 10

a = StarManager()

a.runSingleCase("case", baseGeometryDict, Path.cwd() / "cases", Path.cwd() / "refFiles")