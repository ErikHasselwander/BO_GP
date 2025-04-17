import numpy as np
from pathlib import Path
from io import TextIOWrapper

from SGMG.geometry_storage import GeometryStorage, Sketch, Curve
from SGMG.generate_macro_bindings import macro_bindings


class StarGeometryMacroGenerator:
    def __init__(
        self, geometry: GeometryStorage, fileName: str, path=Path.cwd()
    ) -> Path:
        if fileName[-5:] != ".java":
            fileName += ".java"
        self.filePath = path / fileName
        self.sketches = {}

        with open(self.filePath, "w+") as macroFile:
            macro_bindings.write_entry(
                macroFile, fileName, len(geometry.get_sketches())
            )
            macroFile.write("\n")

            for index, sketch in enumerate(geometry.get_sketches().values()):
                self.__add_sketch(sketch, macroFile, index)

            macro_bindings.write_end(
                macroFile, len(geometry.get_sketches()), geometry.name
            )

    def getPath(self):
        return self.filePath

    def __add_sketch(self, sketch: Sketch, macroFile: TextIOWrapper, sketchNumber: int):
        if sketch.name in self.sketches:
            print("ERROR: sketch already exists")
        self.sketches[sketch.name] = {"points": {}, "curves": [""] * sketch.length()}
        macro_bindings.write_sketch_start(macroFile, sketchNumber, sketch.name)
        macroFile.write("\n")

        # Add all unique points from all curves to the points list
        i = 0
        for curveIndex, curveData in enumerate(sketch.curves):
            self.sketches[sketch.name]["curves"][curveIndex] = {
                "faceName": curveData.face_name,
                "lines": [],
            }
            for point in curveData.points:
                pointTuple = tuple(point)
                if pointTuple not in self.sketches[sketch.name]["points"]:
                    self.sketches[sketch.name]["points"][pointTuple] = i
                    i += 1
        if len(self.sketches[sketch.name]["points"]) > 900:
            print(
                f"WARNING: Sketch {sketch.name} contains more than 900 points ({len(self.sketches[sketch.name]["points"])} points). Macro unlikely to compile. \n Consider decreasing resolution or splitting sketch into multiple regions."
            )
        # Write points to the file
        for pointTuple, index in self.sketches[sketch.name]["points"].items():
            macroFile.write(
                f"    PointSketchPrimitive {sketch.name}Point{index} = {sketch.name}.createPoint(new DoubleVector(new double[] {{{pointTuple[0]}, {pointTuple[1]}}}));\n"
            )
        macroFile.write("\n")

        # Write all edges, and add each segments to their respective namned buckets
        i = 0
        for curveIndex, curveData in enumerate(sketch.curves):
            points = curveData.points
            for k in range(len(points) - 1):
                pointTuplek = tuple(points[k])
                pointTuplel = tuple(points[k + 1])
                if pointTuplek == pointTuplel:
                    continue
                lineName = f"{sketch.name}Line{i}"
                macroFile.write(
                    f"    LineSketchPrimitive {lineName} = {sketch.name}.createLine({sketch.name}Point{self.sketches[sketch.name]["points"][pointTuplek]}, {sketch.name}Point{self.sketches[sketch.name]["points"][pointTuplel]});\n"
                )
                self.sketches[sketch.name]["curves"][curveIndex]["lines"].append(
                    lineName
                )
                i += 1
        macroFile.write("\n")

        # End sketch
        macro_bindings.end_sketching(macroFile, sketch.name)
        macroFile.write("\n")

        # Extrude the shape
        extrusionName = f"extrusionMerge_{sketch.name}"
        macro_bindings.write_extrude_sketch(macroFile, sketch.name, extrusionName)
        macroFile.write("\n")

        # Name the body
        random_line = self.sketches[sketch.name]["curves"][curveIndex]["lines"][0]
        cadbodyName = f"cadbody_{sketch.name}"
        macroFile.write(
            f"    star.cadmodeler.Body {cadbodyName} = ((star.cadmodeler.Body) extrusionMerge_{sketch.name}.getBody({random_line}));\n"
        )
        macroFile.write(f'    {cadbodyName}.setPresentationName("{sketch.name}");\n\n')
        # and the surfs
        macroFile.write(
            f"    Face face_0 = ((Face) {extrusionName}.getEndCapFace({random_line}));"
        )
        macroFile.write(
            f'    cadModel_0.setFaceNameAttributes(new ArrayList<>(Arrays.<Face>asList(face_0)), "2dsurf2", false);'
        )
        macroFile.write(
            f"    Face face_1 = ((Face) {extrusionName}.getStartCapFace({random_line}));"
        )
        macroFile.write(
            f'    cadModel_0.setFaceNameAttributes(new ArrayList<>(Arrays.<Face>asList(face_1)), "2dsurf1", false);'
        )

        # Create all sideFaces and add them to the global map
        sidefaces = {}
        for curveIndex, curveData in enumerate(sketch.curves):
            faceName = curveData.face_name
            if faceName not in sidefaces:
                sidefaces[faceName] = []
            curveLines = self.sketches[sketch.name]["curves"][curveIndex]["lines"]
            for curveLine in curveLines:
                curveLineName = "face_" + curveLine
                macroFile.write(
                    f'    Face {curveLineName} = ((Face) {extrusionName}.getSideFace({curveLine},"True"));\n'
                )
                sidefaces[faceName].append(curveLineName)
        macroFile.write(f"\n")

        for faceName, faceNames in sidefaces.items():
            cleandFaceNames = ", ".join(faceNames)
            macroFile.write(
                f'    cadModel_0.setFaceNameAttributes(new ArrayList<>(Arrays.<Face>asList({cleandFaceNames})), "{faceName}", false);\n'
            )
        macroFile.write(f"  }}\n")
        macroFile.write("\n")
