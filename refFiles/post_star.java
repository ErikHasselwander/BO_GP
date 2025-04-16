// STAR-CCM+ macro: Report_to_csv.java
package macro;

import java.io.*;
import java.nio.*;
import java.util.*;
import star.base.neo.*;
import star.base.report.*;
import star.common.*;
import star.flow.*;
import star.vis.*;
import star.meshing.*;

public class post_star extends StarMacro {
  BufferedWriter bwout = null;

  public void execute() {
    execute0();
    execute1();
    execute2();
  }

  private void execute0() {
    Simulation simulation_0 = getActiveSimulation();
    String outPutDir = simulation_0.getSessionDir();

    for (StarPlot plot : simulation_0.getPlotManager().getPlots()) {
      plot.openInteractive();
      String filePath = outPutDir + "/" + "plot_" + plot.getPresentationName() + ".png";
      plot.encode(resolvePath(filePath), "png", 800, 600, true, true);
      simulation_0.println("Saved: " + filePath);
    }

    for (Scene scene : simulation_0.getSceneManager().getScenes()) {
      String filePath = outPutDir + "/" + scene.getPresentationName() + ".png";
      scene.printAndWait(resolvePath(filePath), 1, 1280, 720);
      simulation_0.println("Saved: " + filePath);
    }
  }

  public void execute1() {
    try {
      Simulation simulation_0 = getActiveSimulation();

      // Collecting the simualtion file name
      String simulationName = simulation_0.getPresentationName();
      simulation_0.println("Simulation Name:" + simulationName);

      // Open Buffered Input and Output Readers
      // Creating file with name "<sim_file_name>+report.csv"
      BufferedWriter bwout = new BufferedWriter(new FileWriter(resolvePath(simulation_0.getSessionDir() + "/" + "results.csv")));
      bwout.write("Report Name, Value, Unit, \n");

      Collection<Report> reportCollection = simulation_0.getReportManager().getObjects();

      for (Report thisReport : reportCollection) {
        String fieldLocationName = thisReport.getPresentationName();
        Double fieldValue = thisReport.getReportMonitorValue();
        String fieldUnits = thisReport.getUnits().toString();

        // Printing to chek in output window
        simulation_0.println("Field Location :" + fieldLocationName);
        simulation_0.println(" Field Value :" + fieldValue);
        simulation_0.println(" Field Units :" + fieldUnits);
        simulation_0.println("");

        // Write Output file as "sim file name"+report.csv
        bwout.write(fieldLocationName + ", " + fieldValue + ", " + fieldUnits + "\n");
      }

      Collection<Monitor> monitors = simulation_0.getMonitorManager().getObjects();
      for (Monitor monitor : monitors) {
        if (monitor instanceof ResidualMonitor) {
          ResidualMonitor residualMonitor = (ResidualMonitor) monitor;

          double[] residualValues = residualMonitor.getAllYValues();

          if (residualValues.length > 0) {
            double lastValue = residualValues[residualValues.length - 1];
            bwout.write(residualMonitor.getPresentationName() + ", " + lastValue + ", \n");
          }
        }
      }

      bwout.close();

    } catch (IOException iOException) {
    }
  }

  private void execute2() {

    Simulation simulation_0 = 
      getActiveSimulation();

    Solution solution_0 = 
      simulation_0.getSolution();

    solution_0.clearSolution(Solution.Clear.History, Solution.Clear.Fields, Solution.Clear.LagrangianDem);

    MeshPipelineController meshPipelineController_0 = 
      simulation_0.get(MeshPipelineController.class);

    meshPipelineController_0.clearGeneratedMeshes();
  }

}
