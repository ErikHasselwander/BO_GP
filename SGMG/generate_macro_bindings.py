from io import TextIOWrapper

MODEL_TMP_NAME = "SGMG_TMP_MODEL"


class macro_bindings:
    def __init__(self):
        pass

    def write_entry(macroFile: TextIOWrapper, fileName, numberOfSketches):
        macroFile.write(f"// Simcenter STAR-CCM+ macro: {fileName}\n")
        macroFile.write(f"// Written by Erik Hasselwander\n")
        macroFile.write(f"\n")
        macroFile.write(f"package macro;\n")
        macroFile.write(f"import java.util.*;\n")
        macroFile.write(f"import star.common.*;\n")
        macroFile.write(f"import star.base.neo.*;\n")
        macroFile.write(f"import star.cadmodeler.*;\n")
        macroFile.write(f"\n")
        macroFile.write(f"public class {fileName[:-5]} extends StarMacro {{\n")
        macroFile.write(f"\n")
        macroFile.write(f"  public void execute() {{\n")
        for i in range(numberOfSketches + 2):
            macroFile.write(f"    execute{i}();\n")
        macroFile.write(f"  }}\n")
        macroFile.write(f"\n")
        macroFile.write(f"  private void execute{0}() {{\n")
        macroFile.write(f"    Simulation simulation_0 = getActiveSimulation();\n")
        macroFile.write(
            f"    CadModel cadModel_0 = simulation_0.get(SolidModelManager.class).createSolidModel();\n\n"
        )
        macroFile.write(f"    cadModel_0.resetSystemOptions();\n")
        macroFile.write(f'    cadModel_0.setPresentationName("{MODEL_TMP_NAME}");\n')
        macroFile.write(f"  }}\n")

    def write_sketch_start(
        macroFile: TextIOWrapper, sketchNumber: int, sketchName: str
    ):
        macroFile.write(f"  private void execute{sketchNumber+1}() {{\n")
        macroFile.write(f"    Simulation simulation_0 = getActiveSimulation();\n")
        macroFile.write(
            f'    CadModel cadModel_0 = ((CadModel) simulation_0.get(SolidModelManager.class).getObject("{MODEL_TMP_NAME}"));\n\n'
        )
        macroFile.write(f"    cadModel_0.resetSystemOptions();\n")
        macroFile.write(
            f'    CanonicalSketchPlane canonicalSketchPlane_0 = ((CanonicalSketchPlane) cadModel_0.getFeature("XY"));\n'
        )
        macroFile.write(
            f"    Units units_0 = simulation_0.getUnitsManager().getPreferredUnits(Dimensions.Builder().length(1).build());\n"
        )
        macroFile.write(
            f'    Units units_1 = ((Units) simulation_0.getUnitsManager().getObject("deg"));\n'
        )
        macroFile.write(
            f"    LabCoordinateSystem labCoordinateSystem_0 = simulation_0.getCoordinateSystemManager().getLabCoordinateSystem();\n"
        )
        macroFile.write(
            f"    Sketch {sketchName} = cadModel_0.getFeatureManager().createSketch(canonicalSketchPlane_0);\n"
        )
        macroFile.write(f"    cadModel_0.allowMakingPartDirty(false);\n")
        macroFile.write(
            f"    cadModel_0.getFeatureManager().startSketchEdit({sketchName});\n"
        )

    def end_sketching(macroFile: TextIOWrapper, sketchName):
        macroFile.write(f"    {sketchName}.setIsUptoDate(true);\n")
        macroFile.write(f"    {sketchName}.markFeatureForEdit();\n")
        macroFile.write(f"    cadModel_0.allowMakingPartDirty(true);\n")
        macroFile.write(
            f"    cadModel_0.getFeatureManager().stopSketchEdit({sketchName}, true);\n"
        )
        macroFile.write(
            f"    cadModel_0.getFeatureManager().updateModelAfterFeatureEdited({sketchName}, null);\n"
        )

    def write_extrude_sketch(
        macroFile: TextIOWrapper, sketchName: str, extrusionName: str, height=0.1
    ):
        macroFile.write(
            f"    ExtrusionMerge {extrusionName} = cadModel_0.getFeatureManager().createExtrusionMerge({sketchName});\n"
        )
        macroFile.write(f"    {extrusionName}.setAutoPreview(true);\n")
        macroFile.write(f"    cadModel_0.allowMakingPartDirty(false);\n")
        macroFile.write(f"    {extrusionName}.setDirectionOption(0);\n")
        macroFile.write(f"    {extrusionName}.setExtrudedBodyTypeOption(0);\n")
        macroFile.write(
            f"    {extrusionName}.getDistance().setValueAndUnits(0.1, units_0);\n"
        )
        macroFile.write(
            f"    {extrusionName}.getDistanceAsymmetric().setValueAndUnits(0.1, units_0);\n"
        )
        macroFile.write(
            f"    {extrusionName}.getOffsetDistance().setValueAndUnits(0.1, units_0);\n"
        )
        macroFile.write(f"    {extrusionName}.setDistanceOption(0);\n")
        macroFile.write(f"    {extrusionName}.setCoordinateSystemOption(0);\n")
        macroFile.write(
            f"    {extrusionName}.getDraftAngle().setValueAndUnits(10.0, units_1);\n"
        )
        macroFile.write(f"    {extrusionName}.setDraftOption(0);\n")
        macroFile.write(
            f"    {extrusionName}.setImportedCoordinateSystem(labCoordinateSystem_0);\n"
        )
        macroFile.write(
            f"    {extrusionName}.getDirectionAxis().setCoordinateSystem(labCoordinateSystem_0);\n"
        )
        macroFile.write(f"    {extrusionName}.getDirectionAxis().setUnits0(units_0);\n")
        macroFile.write(f"    {extrusionName}.getDirectionAxis().setUnits1(units_0);\n")
        macroFile.write(f"    {extrusionName}.getDirectionAxis().setUnits2(units_0);\n")
        macroFile.write(f'    {extrusionName}.getDirectionAxis().setDefinition("");\n')
        macroFile.write(
            f"    {extrusionName}.getDirectionAxis().setValue(new DoubleVector(new double[] {{0.0, 0.0, 1.0}}));\n"
        )
        macroFile.write(f"    {extrusionName}.setFace(null);\n")
        macroFile.write(f"    {extrusionName}.setBody(null);\n")
        macroFile.write(f"    {extrusionName}.setPlane(null);\n")
        macroFile.write(f"    {extrusionName}.setFeatureInputType(0);\n")
        macroFile.write(
            f"    {extrusionName}.setInputFeatureEdges(new ArrayList<>(Collections.<Edge>emptyList()));\n"
        )
        macroFile.write(f"    {extrusionName}.setSketch({sketchName});\n")
        macroFile.write(
            f"    {extrusionName}.setInteractingBodies(new ArrayList<>(Collections.<Body>emptyList()));\n"
        )
        macroFile.write(
            f"    {extrusionName}.setInteractingBodiesBodyGroups(new ArrayList<>(Collections.<BodyGroup>emptyList()));\n"
        )
        macroFile.write(
            f"    {extrusionName}.setInteractingBodiesCadFilters(new ArrayList<>(Collections.<CadFilter>emptyList()));\n"
        )
        macroFile.write(f"    {extrusionName}.setInteractingSelectedBodies(false);\n")
        macroFile.write(f"    {extrusionName}.setPostOption(0);\n")
        macroFile.write(f"    {extrusionName}.setExtrusionOption(0);\n")
        macroFile.write(f"    {extrusionName}.setIsBodyGroupCreation(false);\n")
        macroFile.write(
            f"    cadModel_0.getFeatureManager().markDependentNotUptodate({extrusionName});\n"
        )
        macroFile.write(f"    cadModel_0.allowMakingPartDirty(true);\n")
        macroFile.write(f"    {extrusionName}.markFeatureForEdit();\n")
        macroFile.write(
            f"    cadModel_0.getFeatureManager().execute({extrusionName});\n"
        )

    def write_end(macroFile: TextIOWrapper, numberOfSketches, modelName):
        macroFile.write(f"  private void execute{numberOfSketches+1}() {{\n")
        macroFile.write(f"    Simulation simulation_0 = getActiveSimulation();\n")
        macroFile.write(
            f'    CadModel cadModel_0 = ((CadModel) simulation_0.get(SolidModelManager.class).getObject("{MODEL_TMP_NAME}"));\n\n'
        )
        macroFile.write(f"    cadModel_0.resetSystemOptions();\n")
        macroFile.write(f'    cadModel_0.setPresentationName("{modelName}");\n')
        macroFile.write(f"  }}\n")
        macroFile.write(f"}}\n")
