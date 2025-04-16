###############################################################################
##                                                                           ##
## This file contains object definitions for geometric parametrization and   ##
## meshing for ducts.                                                        ##
##                                                                           ##
## Author: Alexandre Capitao Patrao, 2022-03-17                              ##
## capitao@chalmers.se                                                       ##
##                                                                           ##
###############################################################################

import numpy as np
from scipy.special import binom
from pathlib import Path
import subprocess
import os
import sys

import matplotlib.pyplot as plt

from SGMG.geometry_storage import GeometryStorage, Sketch, Curve


def bezierCurve(bezierPoints, numPoints=100, selfIntersectFlag=False):
    tVal = np.linspace(0, 1, num=numPoints)
    pAnalytic = np.zeros((len(tVal), len(bezierPoints[0])))
    order = len(bezierPoints) - 1
    for k in range(len(bezierPoints[0])):
        for j in range(len(tVal)):
            for i in range(order + 1):
                t = tVal[j]
                pAnalytic[j][k] = (
                    pAnalytic[j][k]
                    + binom(order, i)
                    * (1 - t) ** (order - i)
                    * t**i
                    * bezierPoints[i][k]
                )

    if selfIntersectFlag:
        foundIntersection, intersection = checkIfCurveSelfIntersects(pAnalytic)
        if foundIntersection:
            print("\t\tBezier curve self-intersects!")
        return pAnalytic, foundIntersection, intersection
    else:
        return pAnalytic, None, None


def checkIfCurveSelfIntersects(curve):
    np.seterr(divide="ignore")

    foundIntersection = False
    intersection = None
    for i in range(len(curve) - 1):  # loop through all curve segments, pick segment 1
        # pick segment 1
        p1 = curve[i, :]
        p2 = curve[i + 1, :]

        for j in range(
            len(curve) - 1
        ):  # loop through all curve segments, pick segment 2
            if i != j:
                # pick segment 2
                p3 = curve[j, :]
                p4 = curve[j + 1, :]

                # check if intersect
                # https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
                r = p2 - p1
                s = p4 - p3
                p = p1
                q = p3
                t = np.cross((q - p), s) / np.cross(r, s)
                u = np.cross((q - p), r) / np.cross(r, s)

                if t > 0 and t < 1 and u > 0 and u < 1:
                    intersection = p + t * r
                    foundIntersection = True
                    print("\t\tCurve self-intersects!")
                    break

            if abs(i - j) == 1:
                # neighbour segment, wont intersect except at ends of curves, so do nothing
                pass
            else:
                # same segment as segment 1
                pass

        # break outer loop in case inner loops finds self-intersection
        if foundIntersection:
            break

    return foundIntersection, intersection


class HEXTestrigDuctCurvedFinsGeometry:  # class definition containing the geometry for a duct in terms of bezier curves
    def __init__(self, baseGeometryDict, designVariablesDict):
        # Prepare geometry storage
        self.geometry_storage = GeometryStorage("HEXTestrigDuctCurvedFinsGeometry")
        self.inlet_sketch = Sketch("inlet_section")
        self.hex_sketch = Sketch("hex_section")
        self.outlet_sketch = Sketch("outlet_section")

        self.RhInlet = baseGeometryDict["RhInlet"]
        self.RtInlet = baseGeometryDict["RtInlet"]
        self.RhOutlet = baseGeometryDict["RhOutlet"]
        self.RtOutlet = baseGeometryDict["RtOutlet"]
        self.deltaR_L = baseGeometryDict["deltaR_L"]



        # initial sizing for hex
        self.rMidInlet = 0.5 * (self.RtInlet + self.RhInlet)
        self.rMidOutlet = 0.5 * (self.RtOutlet + self.RhOutlet)
        self.LtotalDucts = (
            0.5 * (self.RtInlet + self.RhInlet) - 0.5 * (self.RtOutlet + self.RhOutlet)
        ) / self.deltaR_L

        baseGeometryDict["P_A"] = np.array([0.3650 - 0.3600, self.RhInlet])
        baseGeometryDict["P_A_tangent"] = np.array([0.96143577, -0.27502955])
        baseGeometryDict["P_B"] = np.array([0, self.RtInlet])
        baseGeometryDict["P_B_tangent"] = np.array([0.99432634, -0.10637258])
        baseGeometryDict["P_C"] = np.array([self.LtotalDucts, self.RtOutlet])
        baseGeometryDict["P_C_tangent"] = np.array([-1, 0])
        baseGeometryDict["P_D"] = np.array([self.LtotalDucts, self.RhOutlet])
        baseGeometryDict["P_D_tangent"] = np.array([-1, 0])
        self.inletLength = 0  # fixed length
        self.outletLength = 0  # fixed length
        baseGeometryDict["P_I"] = np.array(
            [baseGeometryDict["P_C"][0] + self.outletLength, baseGeometryDict["P_C"][1]]
        )
        baseGeometryDict["P_J"] = np.array(
            [baseGeometryDict["P_D"][0] + self.outletLength, baseGeometryDict["P_D"][1]]
        )
        baseGeometryDict["P_K"] = np.array(
            [baseGeometryDict["P_A"][0] - self.inletLength, baseGeometryDict["P_A"][1]]
        )
        baseGeometryDict["P_L"] = np.array(
            [baseGeometryDict["P_B"][0] - self.inletLength, baseGeometryDict["P_B"][1]]
        )

        ## Design parameters
        self.xMid = (
            designVariablesDict["xMidFactor"] * self.LtotalDucts
        )  # [m] axial position for the midpoint of the hex
        self.rMid = self.rMidOutlet + designVariablesDict["rMidFactor"] * (
            self.rMidInlet - self.rMidOutlet
        )  # [m] radial position for the midpoint of the hex
        self.alpha = designVariablesDict["alpha"] * np.pi / 180
        self.kappa = designVariablesDict["kappa"] * np.pi / 180
        self.rCurvedFin = baseGeometryDict["Lx"] / np.sin(self.kappa)
        self.fin_n = self.rCurvedFin * (1 - np.cos(np.arcsin(0.5 * np.sin(self.kappa))))
        self.fin_m = baseGeometryDict["Lx"] * np.tan(self.kappa / 2)
        self.finThetaVector = np.linspace(0, self.kappa, 50)
        self.finLocalX = self.rCurvedFin * np.cos(self.finThetaVector)
        self.finLocalY = self.rCurvedFin * np.sin(self.finThetaVector)
        self.finLocal = np.array([self.finLocalX, self.finLocalY]).transpose()

        # duct endpoints and tangents
        self.P_A = baseGeometryDict["P_A"]
        self.P_A_tangent = baseGeometryDict["P_A_tangent"]
        self.P_B = baseGeometryDict["P_B"]
        self.P_B_tangent = baseGeometryDict["P_B_tangent"]
        self.P_C = baseGeometryDict["P_C"]
        self.P_C_tangent = baseGeometryDict["P_C_tangent"]
        self.P_D = baseGeometryDict["P_D"]
        self.P_D_tangent = baseGeometryDict["P_D_tangent"]

        self.P_I = baseGeometryDict["P_I"]  # additional downstream point for outlet
        self.P_J = baseGeometryDict["P_J"]  # additional downstream point for outlet

        self.P_K = baseGeometryDict["P_K"]  # additional downstream point for outlet
        self.P_L = baseGeometryDict["P_L"]  # additional downstream point for inlet

        # HEX corner points
        # hex centroid
        self.P_Mid = np.array([self.xMid, self.rMid])
        self.Ly = baseGeometryDict["A_HEX_inlet"] / (2 * np.pi * self.rMid)

        self.xh = (
            self.xMid
            - (0.5 * self.Ly - self.fin_n) * np.cos(self.alpha)
            + 0.5 * baseGeometryDict["Lx"] * np.sin(self.alpha)
        )
        self.rh = (
            self.rMid
            - (0.5 * self.Ly - self.fin_n) * np.sin(self.alpha)
            - 0.5 * baseGeometryDict["Lx"] * np.cos(self.alpha)
        )
        self.P_H = np.array([self.xh, self.rh])
        self.P_H_tangent = np.array([np.sin(self.alpha), -np.cos(self.alpha)])

        self.xe = (
            self.xMid
            - (0.5 * self.Ly + (self.fin_m - self.fin_n)) * np.cos(self.alpha)
            - 0.5 * baseGeometryDict["Lx"] * np.sin(self.alpha)
        )
        self.re = (
            self.rMid
            - (0.5 * self.Ly + (self.fin_m - self.fin_n)) * np.sin(self.alpha)
            + 0.5 * baseGeometryDict["Lx"] * np.cos(self.alpha)
        )
        self.P_E = np.array([self.xe, self.re])
        self.P_E_tangent = np.array(
            [-np.sin(self.alpha + self.kappa), np.cos(self.alpha + self.kappa)]
        )

        self.xf = (
            self.xMid
            + (0.5 * self.Ly - (self.fin_m - self.fin_n)) * np.cos(self.alpha)
            - 0.5 * baseGeometryDict["Lx"] * np.sin(self.alpha)
        )
        self.rf = (
            self.rMid
            + (0.5 * self.Ly - (self.fin_m - self.fin_n)) * np.sin(self.alpha)
            + 0.5 * baseGeometryDict["Lx"] * np.cos(self.alpha)
        )
        self.P_F = np.array([self.xf, self.rf])
        self.P_F_tangent = np.array(
            [-np.sin(self.alpha + self.kappa), np.cos(self.alpha + self.kappa)]
        )

        self.xg = (
            self.xMid
            + (0.5 * self.Ly + self.fin_n) * np.cos(self.alpha)
            + 0.5 * baseGeometryDict["Lx"] * np.sin(self.alpha)
        )
        self.rg = (
            self.rMid
            + (0.5 * self.Ly + self.fin_n) * np.sin(self.alpha)
            - 0.5 * baseGeometryDict["Lx"] * np.cos(self.alpha)
        )
        self.P_G = np.array([self.xg, self.rg])
        self.P_G_tangent = np.array([np.sin(self.alpha), -np.cos(self.alpha)])

        # curved fins and endwall curves
        self._hexRotMatrix = np.array(
            [
                [np.cos(self.alpha), -np.sin(self.alpha)],
                [np.sin(self.alpha), np.cos(self.alpha)],
            ]
        )
        self._C15_temp1 = self.finLocal.copy()
        self._C15_temp1[:, 0] = (
            self._C15_temp1[:, 0] - self._C15_temp1[0, 0]
        )  # translate into "position" so that lower end of curve is at 0,0
        self._C15_temp2 = np.matmul(
            self._hexRotMatrix, self._C15_temp1.transpose()
        ).transpose()
        self._C15_temp2[:, 0] = self._C15_temp2[:, 0] + self.P_H[0]
        self._C15_temp2[:, 1] = self._C15_temp2[:, 1] + self.P_H[1]
        self.C15 = self._C15_temp2

        self._C16_temp1 = self.finLocal.copy()
        self._C16_temp1[:, 0] = (
            self._C16_temp1[:, 0] - self._C16_temp1[0, 0]
        )  # translate into "position" so that lower end of curve is at 0,0
        self._C16_temp2 = np.matmul(
            self._hexRotMatrix, self._C16_temp1.transpose()
        ).transpose()
        self._C16_temp2[:, 0] = self._C16_temp2[:, 0] + self.P_G[0]
        self._C16_temp2[:, 1] = self._C16_temp2[:, 1] + self.P_G[1]
        self.C16 = self._C16_temp2

        # construt the additional Bezier control points
        self.axialLengthScale1 = np.linalg.norm(self.P_A - self.P_E)
        self.axialLengthScale2 = np.linalg.norm(self.P_B - self.P_F)
        self.axialLengthScale3 = np.linalg.norm(self.P_B - self.P_F)
        self.axialLengthScale4 = np.linalg.norm(self.P_G - self.P_C)
        self.axialLengthScale5 = np.linalg.norm(self.P_G - self.P_C)
        self.axialLengthScale6 = np.linalg.norm(self.P_H - self.P_D)
        self.axialLengthScale7 = np.linalg.norm(self.P_H - self.P_D)
        self.axialLengthScale8 = np.linalg.norm(self.P_A - self.P_E)
        self.P_1 = (
            self.P_A
            + self.P_A_tangent * designVariablesDict["lambda1"] * self.axialLengthScale1
        )
        self.P_2 = (
            self.P_B
            + self.P_B_tangent * designVariablesDict["lambda2"] * self.axialLengthScale2
        )
        self.P_3 = (
            self.P_F
            + self.P_F_tangent * designVariablesDict["lambda3"] * self.axialLengthScale3
        )
        self.P_4 = (
            self.P_G
            + self.P_G_tangent * designVariablesDict["lambda4"] * self.axialLengthScale4
        )
        self.P_5 = (
            self.P_C
            + self.P_C_tangent * designVariablesDict["lambda5"] * self.axialLengthScale5
        )
        self.P_6 = (
            self.P_D
            + self.P_D_tangent * designVariablesDict["lambda6"] * self.axialLengthScale6
        )
        self.P_7 = (
            self.P_H
            + self.P_H_tangent * designVariablesDict["lambda7"] * self.axialLengthScale7
        )
        self.P_8 = (
            self.P_E
            + self.P_E_tangent * designVariablesDict["lambda8"] * self.axialLengthScale8
        )

        # additional bezier points
        # self.P_9 = np.array([self.P_A[0] + designVariablesDict['lambda9']*(self.P_E[0] - self.P_A[0]), 0.5*(self.P_A[1] + self.P_E[1]) + designVariablesDict['lambda10']*self.P_A[1]])
        # self.P_10 = np.array([self.P_B[0] + designVariablesDict['lambda11']*(self.P_F[0] - self.P_B[0]), 0.5*(self.P_B[1] + self.P_F[1]) + designVariablesDict['lambda12']*self.P_B[1]])
        # self.P_11 = np.array([self.P_G[0] + designVariablesDict['lambda13']*(self.P_C[0] - self.P_G[0]), 0.5*(self.P_G[1] + self.P_C[1]) + designVariablesDict['lambda14']*self.P_C[1]])
        # self.P_12 = np.array([self.P_H[0] + designVariablesDict['lambda15']*(self.P_D[0] - self.P_H[0]), 0.5*(self.P_H[1] + self.P_D[1]) + designVariablesDict['lambda16']*self.P_D[1]])

        # Generate Bezier curves
        self.C1, _, _ = bezierCurve(
            [self.P_A, self.P_1, self.P_8, self.P_E],
            selfIntersectFlag=True,
            numPoints=200,
        )
        self.C2, _, _ = bezierCurve(
            [self.P_B, self.P_2, self.P_3, self.P_F],
            selfIntersectFlag=True,
            numPoints=200,
        )
        # self.C1, _, _ = bezierCurve([self.P_A, self.P_1, self.P_9, self.P_8, self.P_E], selfIntersectFlag=True, numPoints=200)
        # self.C2, _, _ = bezierCurve([self.P_B, self.P_2, self.P_10, self.P_3, self.P_F], selfIntersectFlag=True, numPoints=200)
        self.C3, _, _ = bezierCurve(
            [self.P_G, self.P_4, self.P_5, self.P_C],
            selfIntersectFlag=True,
            numPoints=200,
        )
        self.C4, _, _ = bezierCurve(
            [self.P_H, self.P_7, self.P_6, self.P_D],
            selfIntersectFlag=True,
            numPoints=200,
        )
        # self.C3, _, _ = bezierCurve([self.P_G, self.P_4, self.P_11, self.P_5, self.P_C], selfIntersectFlag=True, numPoints=200)
        # self.C4, _, _ = bezierCurve([self.P_H, self.P_7, self.P_12, self.P_6, self.P_D], selfIntersectFlag=True, numPoints=200)
        self.C5, _, _ = bezierCurve([self.P_D, self.P_C], numPoints=5)
        self.C6, _, _ = bezierCurve([self.P_D, self.P_J], numPoints=5)
        self.C7, _, _ = bezierCurve([self.P_C, self.P_I], numPoints=5)
        self.C8, _, _ = bezierCurve([self.P_I, self.P_J], numPoints=5)
        self.C9, _, _ = bezierCurve([self.P_L, self.P_K], numPoints=5)
        self.C10, _, _ = bezierCurve([self.P_K, self.P_A], numPoints=5)
        self.C11, _, _ = bezierCurve([self.P_L, self.P_B], numPoints=5)
        self.C12, _, _ = bezierCurve([self.P_A, self.P_B], numPoints=5)
        self.C13, _, _ = bezierCurve([self.P_E, self.P_F], numPoints=5)
        self.C14, _, _ = bezierCurve([self.P_H, self.P_G], numPoints=5)
        # self.C15, _, _ = bezierCurve([self.P_E, self.P_H], numPoints=5)
        # self.C16, _, _ = bezierCurve([self.P_F, self.P_G], numPoints=5)

        self.inlet_sketch.add_curve(Curve(self.C9, "inlet"))
        self.inlet_sketch.add_curve(Curve(self.C10, "wall"))
        self.inlet_sketch.add_curve(Curve(self.C11, "wall"))
        self.inlet_sketch.add_curve(Curve(self.C1, "wall"))
        self.inlet_sketch.add_curve(Curve(self.C2, "wall"))
        self.inlet_sketch.add_curve(Curve(self.C13, "interface"))
        self.geometry_storage.add_sketch(self.inlet_sketch)

        self.hex_sketch.add_curve(Curve(self.C13, "in_interface"))
        self.hex_sketch.add_curve(Curve(self.C14, "out_interface"))
        self.hex_sketch.add_curve(Curve(self.C15, "wall"))
        self.hex_sketch.add_curve(Curve(self.C16, "wall"))
        self.geometry_storage.add_sketch(self.hex_sketch)

        self.outlet_sketch.add_curve(Curve(self.C8, "outlet"))
        self.outlet_sketch.add_curve(Curve(self.C3, "wall"))
        self.outlet_sketch.add_curve(Curve(self.C4, "wall"))
        self.outlet_sketch.add_curve(Curve(self.C6, "wall"))
        self.outlet_sketch.add_curve(Curve(self.C7, "wall"))
        self.outlet_sketch.add_curve(Curve(self.C14, "interface"))
        self.geometry_storage.add_sketch(self.outlet_sketch)

        # List points
        self.listOfPointNames = [
            "P_A",
            "P_B",
            "P_C",
            "P_D",
            "P_E",
            "P_F",
            "P_G",
            "P_H",
            "P_I",
            "P_J",
            "P_1",
            "P_2",
            "P_3",
            "P_4",
            "P_5",
            "P_6",
            "P_7",
            "P_8",
        ]
        self.listOfCurveNames = []
        for i in range(16):
            self.listOfCurveNames.append("C" + str(int(i + 1)))

        # Gather all points that will be used for assoc in one list
        self.POINTS_ASSOC = [
            self.P_A,
            self.P_B,
            self.P_C,
            self.P_D,
            self.P_E,
            self.P_F,
            self.P_G,
            self.P_H,
            self.P_I,
            self.P_J,
            self.P_K,
            self.P_L,
        ]

    def plot(self, workingDir):
        # plot points
        plt.figure(figsize=(16, 9))
        plt.ioff()
        plt.plot(self.P_Mid[0], self.P_Mid[1], "k+", label="P_A")
        for pointName in self.listOfPointNames:
            self.currentPointToPlot = getattr(self, pointName)
            plt.plot(self.currentPointToPlot[0], self.currentPointToPlot[1], "ko")
            plt.annotate(
                "$" + str(pointName.replace("_", "_{") + "}") + "$",
                (self.currentPointToPlot[0], self.currentPointToPlot[1]),
            )

        for curveName in self.listOfCurveNames:
            self.currentCurveToPlot = getattr(self, curveName)
            self.curveMidPoint = int(np.floor(len(self.currentCurveToPlot) / 2))
            plt.plot(self.currentCurveToPlot[:, 0], self.currentCurveToPlot[:, 1])
            plt.annotate(
                "$" + str(curveName) + "$",
                (
                    self.currentCurveToPlot[self.curveMidPoint, 0],
                    self.currentCurveToPlot[self.curveMidPoint, 1],
                ),
            )

        plt.axis("equal")
        self.imagePath = workingDir / "geometry.pdf"
        plt.savefig(self.imagePath, dpi=300)
        plt.close()

    def write_csv():
        pass

    def plot_geometry(self):
        return self.geometry_storage.plot_geometry()


def main():
    Lx = 2
    geom = HEXTestrigDuctCurvedFinsGeometry(
        HInlet=0.1,
        Lx=Lx,
        AR=4,
        DeltaR=0.8*Lx,
        LInlet=0.4,
        LHEX=0.2,
        LOutlet=0.4,
        alpha=-20,
        beta=20,
        l1=0.05,
        l2=0.4,
        l3=0.4,
        l4=0.05
    )
    fig, ax = geom.plot_geometry()
    ax.axis("equal")
    plt.show()


if __name__ == "__main__":
    main()
