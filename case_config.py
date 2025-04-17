import os
import subprocess
import csv
import shutil

import numpy as np
from pathlib import Path
from datetime import datetime
import pandas as pd

from geometryParametrization import HEXTestrigDuctCurvedFinsGeometry
from SGMG.star_geometry_macro_generator import StarGeometryMacroGenerator


class StarManager:
    def __init__(self):
        self.baseGeometryDict = {}
        self.batchCommands = []

    def __setBaseSettings(self):
        self.STARCCMPath = "starccm+"
        self.baseCaseFileName = "basecase_curved_hexmodel_newstar.sim"
        self.nCPUs = 2

    def __setBaseGeometry(self):
        # Radial coordinates for the duct
        self.baseGeometryDict["RtInlet"] = 0.557460964
        self.baseGeometryDict["RhInlet"] = 0.474471390
        self.baseGeometryDict["RtOutlet"] = 0.4103
        self.baseGeometryDict["RhOutlet"] = 0.2876

        # Length of the HEX only
        self.baseGeometryDict["Lx"] = 0.09
        # Variation of duct mid-radius over duct length
        self.baseGeometryDict["deltaR_L"] = 0.2
        self.baseGeometryDict["kappa"] = 0.0001

        self.starInputDict = {}
        self.starInputDict["mdot"] = 12.866  # kg/s

        self.optimization_target = "overallDuctPressureLoss"
        self.residual_limit = 1e-3

    def runSingleCase(
        self,
        casename: str,
        designVariablesList: list,
        dataPath: Path,
        refFilesPath: Path,
    ):
        self.caseName = casename
        # Set the folder to run the case in
        self.refFilesPath = refFilesPath
        self.casePath = dataPath / self.caseName
        self.casePath.mkdir(parents=True, exist_ok=True)

        # The static macros
        self.baseGeometryDict["replaceGeometryMacro"] = str(
            self.refFilesPath / "replace_geometry.java"
        )
        self.baseGeometryDict["starPostMacro"] = str(
            self.refFilesPath / "post_star.java"
        )
        self.baseGeometryDict["starRunMacro"] = str(self.refFilesPath / "run_star.java")

        # Set the base parameters (paths etc)
        self.__setBaseSettings()
        # Set the base geometry params (the static description of the case)
        self.__setBaseGeometry()
        var_names = [
            "xMidFactor",
            "rMidFactor",
            "alpha",
            "lambda1",
            "lambda2",
            "lambda3",
            "lambda4",
            "lambda5",
            "lambda6",
            "lambda7",
            "lambda8",
            "AR",
        ]

        # Set the variable geometry params
        self.optimization_parameters = {}
        for key, value in zip(var_names, designVariablesList):
            self.optimization_parameters[key] = value
            self.baseGeometryDict[key] = value

        # Generate the geometry
        self.__print("Generating geometry...")
        self.geometry = HEXTestrigDuctCurvedFinsGeometry(self.baseGeometryDict)
        self.geometry.plot(self.casePath)
        # Generate the geometry macro
        geometryMacroPath = StarGeometryMacroGenerator(
            self.geometry.geometry_storage, f"{self.caseName}_geometry", self.casePath
        ).getPath()

        # Add the design variables we need in star to the dict
        designVariablesForStar = ["alpha", "kappa"]
        for designVariable in self.baseGeometryDict:
            if designVariable in designVariablesForStar:
                self.starInputDict[designVariable] = self.baseGeometryDict[
                    designVariable
                ]
        self.starInputDict["yprimx0"] = self.geometry.P_H[0]
        self.starInputDict["yprimy0"] = self.geometry.P_H[1]
        variableMacroPath = self.__generateVariableMacro(
            self.starInputDict, self.casePath
        )

        self.simFilePath = self.casePath / (self.caseName + ".sim")
        shutil.copy2(self.refFilesPath / self.baseCaseFileName, self.simFilePath)

        # Set batch commands now that we have the paths.
        self.batchCommands.append(geometryMacroPath)
        self.batchCommands.append(self.baseGeometryDict["replaceGeometryMacro"])
        self.batchCommands.append(variableMacroPath)
        self.batchCommands.append(self.baseGeometryDict["starRunMacro"])
        self.batchCommands.append(self.baseGeometryDict["starPostMacro"])

        self.__print("Running...")
        self.__runCase()
        self.__print("Posting...")
        self.resultsPath = self.casePath / "results.csv"

        self.results = self.__dictifyResults(self.resultsPath)
        self.__print("Posting successful")

        self.__postProcess()

        self.data_to_file = {
            "casename": casename,
            **self.optimization_parameters,
            **self.results
        }
        self.databasePath = dataPath / "database.csv"
        # Convert current data to a DataFrame
        new_df = pd.DataFrame([self.data_to_file])

        if os.path.isfile(self.databasePath):
            # Load existing data
            existing_df = pd.read_csv(self.databasePath)

            # Combine columns from both new and existing data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)

            # Write back full DataFrame with updated columns
            combined_df.to_csv(self.databasePath, index=False)
        else:
            # File doesn't exist — just write the new row
            new_df.to_csv(self.databasePath, index=False)

        if self.optimization_target not in self.results:
            return 1
        if (
            "maxAveResidual" in self.results
            and self.results["maxAveResidual"] > self.residual_limit
        ):
            return 1

        return self.results[self.optimization_target]

    def __runCase(self):
        self.logFilePath = self.casePath / "CFD_out.txt"
        self.logErrorFilePath = self.casePath / "CFD_err.txt"
        self.f1 = open(self.logFilePath, "w")
        self.f2 = open(self.logErrorFilePath, "w")
        self.batchCommands = [str(command) for command in self.batchCommands]
        if os.name == "nt":
            self.starRunCommand = f"{self.STARCCMPath} -np {self.nCPUs} -load {self.simFilePath} -batch {",".join(self.batchCommands)}"
        elif os.name == "posix":
            self.starRunCommand = f"{self.STARCCMPath} -load {self.simFilePath} -batch {",".join(self.batchCommands)} -np {self.nCPUs}"
        else:
            print("os.name not recognized as linux")

        proc = subprocess.Popen(
            self.starRunCommand,
            stdout=self.f1,
            stderr=self.f2,
            shell=True,
            cwd=self.casePath,
        )
        proc.wait()
        proc.terminate()

        self.f1.close()
        self.f2.close()

    def __generateVariableMacro(self, starInputDict: dict, path: Path) -> Path:
        macroName = "update_variables"
        macroPath = path / (macroName + ".java")
        with open(macroPath, "w+") as macroFile:
            macroFile.write(f"package macro;\n")
            macroFile.write(f"import java.util.*;\n")
            macroFile.write(f"import star.common.*;\n")
            macroFile.write(f"import star.base.neo.*;\n")
            macroFile.write(f"\n")
            macroFile.write(f"public class {macroName} extends StarMacro {{\n")
            macroFile.write(f"  public void execute() {{\n")
            macroFile.write(f"    execute0();\n")
            macroFile.write(f"  }}\n")
            macroFile.write(f"\n")
            macroFile.write(f"  private void execute0() {{\n")
            macroFile.write(f"    Simulation simulation_0 = getActiveSimulation();\n")
            macroFile.write(f"\n")
            for index, (key, value) in enumerate(starInputDict.items()):
                macroFile.write(
                    f'    ScalarGlobalParameter scalarGlobalParameter_{index} = ((ScalarGlobalParameter) simulation_0.get(GlobalParameterManager.class).getObject("{key}"));\n'
                )
                macroFile.write(
                    f"    scalarGlobalParameter_{index}.getQuantity().setValue({value});\n"
                )
            macroFile.write(f"\n")
            macroFile.write(f"  }}\n")
            macroFile.write(f"}}\n")

        return macroPath

    def __dictifyResults(self, path):
        results_dict = {}
        try:
            with open(path, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)

                for row in reader:
                    # Remove empty strings and strip spaces
                    row = [item.strip() for item in row if item.strip()]
                    if not len(row) or row[0] == "Report Name":
                        continue

                    if len(row) == 2:  # Case: Name, Value (no unit)
                        row.append("")

                    key, value, unit = row
                    results_dict[key] = self.__convertValue(value),
                    
        except:
            return {}

        return results_dict

    def __postProcess(self):
        # Inverse the uniformity to get non-uniformity
        self.results["hexInletPerturbFactor"] = 1 - self.results.get(
            "HEX_inlet_velocity_uniformity", 0
        )

        # Calculate overall duct pressure loss
        ductPressureLoss = (
            (
                self.results.get("inlet_total_pressure_mca", 1e10)
                - self.results.get("HEX_inlet_total_pressure_mca", 0)
            )
            + (
                self.results.get("HEX_outlet_total_pressure_mca", 1e10)
                - self.results.get("outlet_total_pressure_mca", 0)
            )
        ) / self.results.get("inlet_total_pressure_mca", 1e10)
        self.results["ductPressureLoss"] = ductPressureLoss

        overallDuctPressureLoss = (
            self.results.get("inlet_total_pressure_mca", 1e10)
            - self.results.get("outlet_total_pressure_mca", 0)
        ) / self.results.get("inlet_total_pressure_mca", 1e10)
        self.results["overallDuctPressureLoss"] = overallDuctPressureLoss

        residuals = [
            "Continuity",
            "X-momentum",
            "Y-momentum",
            "Energy",
            "Tke",
            "Sdr",
        ]
        maxAveResidual = max([self.results.get(residual, 0) for residual in residuals])
        self.results["maxAveResidual"] = maxAveResidual

    def __convertValue(self, value):
        """Convert numeric strings to float if possible, otherwise return as a string."""
        try:
            return float(value)
        except ValueError:
            return value  # Return as string if not a number

    def __print(self, string):
        timestamp = datetime.now().strftime("%H:%M")
        print(f"[{timestamp}] {self.caseName}: {string}")
