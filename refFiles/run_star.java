// Simcenter STAR-CCM+ macro: test_start.java
// Written by Simcenter STAR-CCM+ 19.06.009
package macro;

import java.util.*;

import star.common.*;
import star.automation.*;

public class run_star extends StarMacro {

  public void execute() {
    execute0();
  }

  private void execute0() {

    Simulation simulation_0 = 
      getActiveSimulation();
    Solution solution_0 = 
      simulation_0.getSolution();

    solution_0.initializeSolution();

    XyzInternalTable xyzInternalTable_0 = 
      ((XyzInternalTable) simulation_0.getTableManager().getTable("XYZ cold temp"));
    XyzInternalTable xyzInternalTable_1 = 
      ((XyzInternalTable) simulation_0.getTableManager().getTable("XYZ hot temp"));

    FvRepresentation fvRepresentation_1 = 
      ((FvRepresentation) simulation_0.getRepresentationManager().getObject("Volume Mesh"));

    xyzInternalTable_0.setRepresentation(fvRepresentation_1);
    xyzInternalTable_1.setRepresentation(fvRepresentation_1);

    xyzInternalTable_0.extract();
    xyzInternalTable_1.extract();

    SimDriverWorkflow simDriverWorkflow_0 = 
      ((SimDriverWorkflow) simulation_0.get(SimDriverWorkflowManager.class).getObject("target_dt_loop"));

    simDriverWorkflow_0.reset();

    simDriverWorkflow_0.execute();
  }
}
