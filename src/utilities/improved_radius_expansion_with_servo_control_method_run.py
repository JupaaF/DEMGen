#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "0.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "June 07, 2025"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

import argparse
import time
import sys
import shutil
import math
import numpy as np
import pathlib

project_src = pathlib.Path(__file__).resolve().parents[1]
if str(project_src) not in sys.path:
    sys.path.insert(0, str(project_src))

import KratosMultiphysics
from KratosMultiphysics import *
from KratosMultiphysics.DEMApplication import *
from KratosMultiphysics.DEMApplication.DEM_analysis_stage import DEMAnalysisStage
from KratosMultiphysics import Logger

from demgen_case_parameters import load_case_parameters
from particles import ParticlePacking, SphericalParticle
from curve_generation import (
    CurveGenerationSettings,
    DENSITY_SWEEP,
    SINGLE_POINT,
    STRESS_SWEEP,
)

if os.path.exists("normalized_kinematic_energy.txt"):
    os.remove("normalized_kinematic_energy.txt")
if os.path.exists("inletPGDEM.mdpa"):
    os.remove("inletPGDEM.mdpa")
if os.path.exists("stress_tensor_0.txt"):
    os.remove("stress_tensor_0.txt")
if os.path.exists("stress_tensor_1.txt"):
    os.remove("stress_tensor_1.txt")
if os.path.exists("inletPGDEM_post_1.mdpa"):
    os.remove("inletPGDEM_post_1.mdpa")
if os.path.exists("stress_tensor_save.txt"):
    os.remove("stress_tensor_save.txt")
if os.path.exists("target_stress.txt"):
    os.remove("target_stress.txt")
if os.path.exists("success.txt"):
    os.remove("success.txt")
''' 
TODO: granular temperature should be made optional
if os.path.exists("granular_temperature_0.txt"):
    os.remove("granular_temperature_0.txt")
'''

class DEMAnalysisStageWithFlush(DEMAnalysisStage):

    def __init__(
        self,
        model,
        project_parameters,
        radius_multiplier,
        initial_packing: ParticlePacking,
        case_parameters,
        flush_frequency=10.0,
    ):
        super().__init__(model, project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        self.parameters = parameters
        self.radius_multiplier = radius_multiplier
        self.normalized_kinematic_energy = 1e10
        self.initial_radii = {
            particle.node_id: particle.radius for particle in initial_packing
        }
        self.case_parameters = case_parameters
        self.start_reset_velocity = False
        self.second_stage_flag = False
        self.is_in_inaccessibale_region2 = False
        self.is_start_servo_control = False

    def Initialize(self):
        super().Initialize()
        self.dt = self.spheres_model_part.ProcessInfo[DELTA_TIME]
        self.final_check_frequency  = int(self.parameters["GraphExportFreq"].GetDouble()/self.parameters["MaxTimeStep"].GetDouble())
        self.final_check_counter = 0
        self.final_check_counter_ini = 0
        self.measured_stress_list = []
        self.target_packing_density = self.case_parameters["servo_target_packing_density"]
        self.tolerance_of_packing_density = self.case_parameters["tolerance_of_packing_density"]
        self.tolerance_of_unbalanced_force = self.case_parameters["tolerance_of_unbalanced_force"]
        self.tolerance_of_target_mean_stress = self.case_parameters["tolerance_of_target_mean_stress"]
        self.minimum_mean_confining_stress = self.case_parameters["minimum_mean_stress"]
        self.ZeroFrictionPhase = False
        self.zero_friction_phase_counter = 0
        self.zero_friction_phase_counter_target = 100
        self.curve_generation = self._GetCurveGenerationSettings()
        self.target_packing_density = self.curve_generation.initial_density
        self.final_target_packing_density = self.curve_generation.final_density
        self.stress_targets = self.curve_generation.stress_targets
        self.stress_target_index = 0
        self.curve_checkpoint_index = 0
        self.density_sweep_phase = "stress_ramp"
        self._SetTargetMeanStress(self.stress_targets[0])

    def _GetCurveGenerationSettings(self):
        raw_settings = self.case_parameters.get("curve_generation")
        if raw_settings is not None:
            return CurveGenerationSettings(**raw_settings)

        target_stresses = self.parameters["BoundingBoxServoLoadingSettings"][
            "BoundingBoxServoLoadingStress"
        ].GetVector()
        target_stress = max(
            sum(target_stresses) / len(target_stresses),
            self.minimum_mean_confining_stress,
        )
        return CurveGenerationSettings(
            mode=SINGLE_POINT,
            initial_density=self.target_packing_density,
            final_density=self.target_packing_density,
            initial_stress=target_stress,
            final_stress=target_stress,
            number_of_steps=1,
        )

    def _SetTargetMeanStress(self, target_stress):
        self.target_mean_stress = target_stress
        self.parameters["BoundingBoxServoLoadingSettings"][
            "BoundingBoxServoLoadingStress"
        ].SetVector([target_stress, target_stress, target_stress])
        self.measured_stress_list.clear()

    def ReadMaterialsFile(self):
        adapted_to_current_os_relative_path = pathlib.Path(self.DEM_parameters["solver_settings"]["material_import_settings"]["materials_filename"].GetString())
        materials_file_abs_path = os.path.join(self.main_path, str(adapted_to_current_os_relative_path))
        with open(materials_file_abs_path, 'r') as materials_file:
            self.DEM_material_parameters = Parameters(materials_file.read())

        self.initial_friction_coefficient = self.DEM_material_parameters["material_relations"][0]["Variables"]["DYNAMIC_FRICTION"].GetDouble()
        self.initial_rolling_friction_coefficient = self.DEM_material_parameters["material_relations"][0]["Variables"]["ROLLING_FRICTION"].GetDouble()
        self.DEM_material_parameters["material_relations"][0]["Variables"]["STATIC_FRICTION"].SetDouble(0.0)
        self.DEM_material_parameters["material_relations"][0]["Variables"]["DYNAMIC_FRICTION"].SetDouble(0.0)
        self.DEM_material_parameters["material_relations"][0]["Variables"]["ROLLING_FRICTION"].SetDouble(0.0)

    def SetResetStart(self):

        self.start_reset_velocity = True

    def SetAllParticleVelocityToZero(self):
        for node in self.spheres_model_part.Nodes:
            node.SetSolutionStepValue(VELOCITY_X, 0.0)
            node.SetSolutionStepValue(VELOCITY_Y, 0.0)
            node.SetSolutionStepValue(VELOCITY_Z, 0.0)

    #TODO: this should be moved to CPP, too expensive to calculate in python
    def GetGranularTemperature(self):
        vel_x = []
        vel_y = []
        vel_z = []
        volume = []
        total_volume = 0.0
        for node in self.spheres_model_part.Nodes:
            vol = 4/3*math.pi*node.GetSolutionStepValue(RADIUS)**3
            volume.append(vol)
            vel_x.append(vol*node.GetSolutionStepValue(VELOCITY_X))
            vel_y.append(vol*node.GetSolutionStepValue(VELOCITY_Y))
            vel_z.append(vol*node.GetSolutionStepValue(VELOCITY_Z))
            total_volume += vol
        mean_vel_x = sum(vel_x)/total_volume
        mean_vel_y = sum(vel_y)/total_volume
        mean_vel_z = sum(vel_z)/total_volume

        T_x = 0.0
        T_y = 0.0
        T_z = 0.0
        max_gran_temp = 0.0
        for V,u,v,w in zip(volume,vel_x,vel_y,vel_z):
            T_x += (u/V-mean_vel_x)**2
            T_y += (v/V-mean_vel_y)**2
            T_z += (w/V-mean_vel_z)**2
            T_p = 1/3*((u/V-mean_vel_x)**2 + (v/V-mean_vel_y)**2 + (w/V-mean_vel_z)**2)
            if T_p > max_gran_temp:
                max_gran_temp = T_p
        T_x /= len(vel_x)
        T_y /= len(vel_y)
        T_z /= len(vel_z)

        return (T_x+T_y+T_z)/3, max_gran_temp

    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()

        if self.final_check_counter_ini == self.final_check_frequency:

            self.final_check_counter_ini = 0

            if self.DEM_parameters["ContactMeshOption"].GetBool():
                self.UpdateIsTimeToPrintInModelParts(True)

        self.final_check_counter_ini += 1

    def OutputSolutionStep(self):

        if not self.start_reset_velocity:
            super().OutputSolutionStep()
        else:
            self.post_utils.ComputeMeanVelocitiesInTrap("Average_Velocity.txt", self.time, self.graphs_path)
            self.DEMFEMProcedures.PrintGraph(self.time)
            self.DEMFEMProcedures.PrintBallsGraph(self.time)
            self.DEMFEMProcedures.PrintAdditionalGraphs(self.time, self._GetSolver())
            self.DEMEnergyCalculator.CalculateEnergyAndPlot(self.time)

        self._GetSolver().PrepareElementsForPrinting()
        if self.DEM_parameters["ContactMeshOption"].GetBool():
            self._GetSolver().PrepareContactElementsForPrinting()

        if self.ZeroFrictionPhase and self.zero_friction_phase_counter == self.zero_friction_phase_counter_target:
            self.zero_friction_phase_counter = 0
            for properties in self.spheres_model_part.Properties:
                for subproperties in properties.GetSubProperties():
                    subproperties[STATIC_FRICTION] = self.initial_friction_coefficient
                    subproperties[DYNAMIC_FRICTION] = self.initial_friction_coefficient
            self.ZeroFrictionPhase = False
        self.zero_friction_phase_counter += 1

        if self.final_check_counter == self.final_check_frequency:

            self.final_check_counter = 0

            self.UpdateFinalPackingVolume()
            self.MeasureTotalPackingDensityOfFinalPacking()

            L_X = self.BoundingBoxMaxX_update - self.BoundingBoxMinX_update
            L_Y = self.BoundingBoxMaxY_update - self.BoundingBoxMinY_update
            L_Z = self.BoundingBoxMaxZ_update - self.BoundingBoxMinZ_update
            side_length = min(L_X, L_Y, L_Z)
            center_x = 0.0
            center_y = 0.0
            center_z = 0.0

            self.normalized_kinematic_energy = self.DEMEnergyCalculator.CalculateNormalizedKinematicEnergy()
            measured_unbalanced_force = self.MeasureSphereForGettingPackingProperties((side_length/2), center_x, center_y, center_z, 'unbalanced_force')
            with open("normalized_kinematic_energy.txt", 'a') as file:
                file.write(str(self.time) + ' ' + str(self.normalized_kinematic_energy) + ' ' + str(measured_unbalanced_force) + '\n')


            packing_state = self._MeasurePackingState()
            mean_stress = packing_state["mean_stress"]
            self._WritePackingState(
                "stress_tensor_1.txt" if self.is_start_servo_control else "stress_tensor_0.txt",
                packing_state,
            )
            self.measured_stress_list.append(mean_stress)
            with open("target_stress.txt", "a") as target_stress_file:
                target_stress_file.write(f"{self.time} {self.target_mean_stress}\n")

            if not self.is_start_servo_control:

                if self.start_reset_velocity:

                    if (
                        self.curve_generation.mode == SINGLE_POINT
                        and (self.final_packing_density - self.target_packing_density)
                        > self.tolerance_of_packing_density
                    ):
                        print("The packing density is higher than the target packing density, the simulation will be terminated.")
                        time.sleep(5)
                        exit(0)

                    if mean_stress < self.target_mean_stress: # (target stress, packing density) in the accessiable region
                        for properties in self.spheres_model_part.Properties:
                            for subproperties in properties.GetSubProperties():
                                subproperties[STATIC_FRICTION] = self.initial_friction_coefficient
                                subproperties[DYNAMIC_FRICTION] = self.initial_friction_coefficient
                        if measured_unbalanced_force < self.tolerance_of_unbalanced_force or abs(mean_stress - self.target_mean_stress) < self.tolerance_of_target_mean_stress:
                            self.second_stage_flag = True
                            if self.curve_generation.mode == SINGLE_POINT:
                                self.WriteOutMdpaFileOfParticles("inletPGDEM.mdpa")
                            self.PrintResultsForGid(self.time)
                            self.is_start_servo_control = True
                            self.parameters["BoundingBoxMoveOption"].SetBool(True)
                            self.parameters["BoundingBoxServoLoadingOption"].SetBool(True)
                            for properties in self.spheres_model_part.Properties:
                                for subproperties in properties.GetSubProperties():
                                    subproperties[ROLLING_FRICTION] = self.initial_rolling_friction_coefficient
                        
                        #self.copy_files_and_run_show_results()
                        #exit(0)
                    elif measured_unbalanced_force < self.tolerance_of_unbalanced_force: # (target stress, packing density) in the inaccessiable region (2)
                        self.second_stage_flag = True
                        if self.curve_generation.mode == SINGLE_POINT:
                            self.WriteOutMdpaFileOfParticles("inletPGDEM.mdpa")
                        self.PrintResultsForGid(self.time)
                        if mean_stress > self.target_mean_stress:
                            self.is_in_inaccessibale_region2 = True
                        self.is_start_servo_control = True
                        self.parameters["BoundingBoxMoveOption"].SetBool(True)
                        self.parameters["BoundingBoxServoLoadingOption"].SetBool(True)
                        for properties in self.spheres_model_part.Properties:
                            for subproperties in properties.GetSubProperties():
                                subproperties[STATIC_FRICTION] = self.initial_friction_coefficient
                                subproperties[DYNAMIC_FRICTION] = self.initial_friction_coefficient
                                subproperties[ROLLING_FRICTION] = self.initial_rolling_friction_coefficient
                        #self.copy_files_and_run_show_results()
                        #exit(0)
                    else:
                        self.SetAllParticleVelocityToZero()
            else: # servo control phase

                mad = 0.0
                if len(self.measured_stress_list) > 5:
                    mad = np.mean([abs(x - self.target_mean_stress) for x in self.measured_stress_list[-5:]])

                mad_threshold = self.tolerance_of_target_mean_stress
                if mad < mad_threshold and len(self.measured_stress_list) > 5:
                    if measured_unbalanced_force < self.tolerance_of_unbalanced_force:
                        self._HandleStableServoState(packing_state)
        self.final_check_counter += 1

    def _MeasurePackingState(self):
        stress_tensor = self.MeasureSphereForGettingGlobalStressTensor()
        mean_stress = sum(stress_tensor[index][index] for index in range(3)) / 3

        stress_tensor_tangential = self.MeasureGlobalStressTensorTangential()
        mean_stress_tangential = sum(
            stress_tensor_tangential[index][index] for index in range(3)
        ) / 3
        tangential_square_sum = sum(
            stress_tensor_tangential[row][column] ** 2
            for row in range(3)
            for column in range(3)
        )
        shear_stress = np.sqrt(1.5 * tangential_square_sum)

        measured_conductivity, measured_conductivity_trace = (
            self.MeasureGlobalConductivityTensor()
        )
        _, second_invariant, measured_fabric_tensor = self.MeasureGlobalFabricTensor()

        return {
            "time": self.time,
            "mean_stress": mean_stress,
            "packing_density": self.final_packing_density,
            "stress_tensor": stress_tensor,
            "mean_coordination_number": self.MeasureGlobalMeanCoordinationNumber(),
            "conductivity_tensor": measured_conductivity,
            "conductivity_trace": measured_conductivity_trace,
            "mean_stress_tangential": mean_stress_tangential,
            "stress_tensor_tangential": stress_tensor_tangential,
            "shear_stress": shear_stress,
            "fabric_tensor": measured_fabric_tensor,
            "fabric_second_invariant": second_invariant,
        }

    def _WritePackingState(self, output_file_name, packing_state):
        values = [
            packing_state["time"],
            packing_state["mean_stress"],
            packing_state["packing_density"],
            *self._FlattenTensor(packing_state["stress_tensor"]),
            packing_state["mean_coordination_number"],
            *self._FlattenTensor(packing_state["conductivity_tensor"]),
            packing_state["conductivity_trace"],
            packing_state["mean_stress_tangential"],
            *self._FlattenTensor(packing_state["stress_tensor_tangential"]),
            packing_state["shear_stress"],
            *self._FlattenTensor(packing_state["fabric_tensor"]),
            packing_state["fabric_second_invariant"],
        ]
        with open(output_file_name, "a") as output_file:
            output_file.write(" ".join(str(value) for value in values) + "\n")

    @staticmethod
    def _FlattenTensor(tensor):
        return [tensor[row][column] for row in range(3) for column in range(3)]

    def _HandleStableServoState(self, packing_state):
        mode = self.curve_generation.mode
        if mode == SINGLE_POINT:
            self._HandleSinglePoint(packing_state)
        elif mode == STRESS_SWEEP:
            self._HandleStressSweep(packing_state)
        elif mode == DENSITY_SWEEP:
            self._HandleDensitySweep(packing_state)
        else:
            raise RuntimeError(f"Unsupported curve generation mode: {mode}")

    def _HandleSinglePoint(self, packing_state):
        print("The stress is stable; checking the target packing density.")
        if self.is_in_inaccessibale_region2:
            self.WriteOutMdpaFileOfParticles("inletPGDEM.mdpa")
            self.copy_files_and_run_show_results()
            exit(0)

        density_error = self.target_packing_density - self.final_packing_density
        if density_error < -self.tolerance_of_packing_density:
            print(
                "The packing density is higher than the target packing density; "
                "the attempt will be terminated."
            )
            time.sleep(5)
            exit(0)
        if density_error > self.tolerance_of_packing_density:
            self._StartZeroFrictionPhase()
            return

        self._SaveCurveCheckpoint(packing_state)
        self._CompleteSimulation()

    def _HandleStressSweep(self, packing_state):
        self._SaveCurveCheckpoint(packing_state)
        if self._AdvanceStressTarget():
            return
        self._CompleteSimulation()

    def _HandleDensitySweep(self, packing_state):
        if self.density_sweep_phase == "stress_ramp":
            if self._AdvanceStressTarget():
                return

            self.density_sweep_phase = "density_increase"
            self.target_packing_density = self.final_target_packing_density
            self.zero_friction_phase_counter_target = 1000
            # This is the first point on the vertical line, not a pressure-ramp
            # checkpoint, so it is intentionally saved.
            self._SaveCurveCheckpoint(packing_state)
        else:
            self._SaveCurveCheckpoint(packing_state)

        if self.is_in_inaccessibale_region2:
            self._CompleteSimulation()

        density_error = self.target_packing_density - self.final_packing_density
        if density_error > self.tolerance_of_packing_density:
            self._StartZeroFrictionPhase()
            return

        if density_error < -self.tolerance_of_packing_density:
            print(
                "The density sweep passed its final target; saving the last "
                "stable packing."
            )
        self._CompleteSimulation()

    def _AdvanceStressTarget(self):
        if self.stress_target_index == len(self.stress_targets) - 1:
            return False
        self.stress_target_index += 1
        self._SetTargetMeanStress(self.stress_targets[self.stress_target_index])
        return True

    def _StartZeroFrictionPhase(self):
        for properties in self.spheres_model_part.Properties:
            for subproperties in properties.GetSubProperties():
                subproperties[STATIC_FRICTION] = 0.0
                subproperties[DYNAMIC_FRICTION] = 0.0
        self.ZeroFrictionPhase = True
        self.zero_friction_phase_counter = 0

    def _SaveCurveCheckpoint(self, packing_state):
        self._WritePackingState("stress_tensor_save.txt", packing_state)

        if self.curve_generation.mode == STRESS_SWEEP:
            output_name = f"inletPGDEM_{round(self.target_mean_stress)}.mdpa"
        elif self.curve_generation.mode == DENSITY_SWEEP:
            density = packing_state["packing_density"]
            output_name = (
                f"inletPGDEM_density_{self.curve_checkpoint_index:03d}_"
                f"{density:.6f}.mdpa"
            )
        else:
            output_name = "inletPGDEM_target.mdpa"

        second_stage_flag = self.second_stage_flag
        self.second_stage_flag = False
        try:
            self.WriteOutMdpaFileOfParticles(output_name)
        finally:
            self.second_stage_flag = second_stage_flag
        self.PrintResultsForGid(self.time)
        self.curve_checkpoint_index += 1

    def _CompleteSimulation(self):
        self.WriteOutMdpaFileOfParticles("inletPGDEM.mdpa")
        with open("success.txt", "w") as success_file:
            success_file.write("Simulation completed successfully.")
        self.copy_files_and_run_show_results()
        exit(0)

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

    def Finalize(self):
        #self.WriteOutMdpaFileOfParticles("inletPGDEM" + str(self.radius_multiplier) + ".mdpa")
        self.WriteOutMdpaFileOfParticles("inletPGDEM.mdpa")
        self.PrintResultsForGid(self.time)
        super().Finalize()

    def PassNormalizedKineticEnergy(self):

        return self.normalized_kinematic_energy

    def MeasureTotalPackingDensityOfFinalPacking(self):

        selected_element_volume = self.MeasureTotalSpheresVolume()

        self.final_packing_density = selected_element_volume / self.final_packing_volume

        print("Currently packing density is {}".format(self.final_packing_density))

    def UpdateFinalPackingVolume(self):

        self.final_packing_volume = (self.BoundingBoxMaxX_update - self.BoundingBoxMinX_update) * \
                                (self.BoundingBoxMaxY_update - self.BoundingBoxMinY_update) * \
                                (self.BoundingBoxMaxZ_update - self.BoundingBoxMinZ_update)

    def WriteOutMdpaFileOfParticles(self, output_file_name):

        if self.second_stage_flag:
            self.clear_old_and_create_new_show_packing_case_folder()
            aim_path_and_name = os.path.join(os.getcwd(), 'show_packing', output_file_name)
        else:
            aim_path_and_name = os.path.join(os.getcwd(), output_file_name)

        element_ids_by_node = {}
        for element in self.spheres_model_part.Elements:
            node_id = element.GetNode(0).Id
            if node_id in element_ids_by_node:
                raise ValueError(f"Multiple elements reference particle node {node_id}.")
            element_ids_by_node[node_id] = element.Id

        particles = ParticlePacking()
        for node in self.spheres_model_part.Nodes:
            try:
                element_id = element_ids_by_node[node.Id]
                initial_radius = self.initial_radii[node.Id]
            except KeyError as error:
                raise ValueError(
                    f"Incomplete IRES particle data for node {node.Id}."
                ) from error

            particles.add(
                SphericalParticle(
                    node_id=node.Id,
                    element_id=element_id,
                    position=(node.X, node.Y, node.Z),
                    radius=initial_radius * self.radius_multiplier,
                )
            )

        unexpected_element_nodes = set(element_ids_by_node) - {
            particle.node_id for particle in particles
        }
        if unexpected_element_nodes:
            raise ValueError(
                "Elements reference missing particle nodes: "
                f"{sorted(unexpected_element_nodes)}."
            )

        particles.write_mdpa(aim_path_and_name)

        print("Successfully write out GID DEM.mdpa file!")

    def clear_old_and_create_new_show_packing_case_folder(self):

        aim_path = os.path.join(os.getcwd(),'show_packing')

        if os.path.exists(aim_path):
            shutil.rmtree(aim_path, ignore_errors=True)
            os.makedirs(aim_path)
        else:
            os.makedirs(aim_path)

    def copy_seed_files_to_aim_folders(self):

        aim_path = os.path.join(os.getcwd(), 'show_packing')

        seed_file_name_list = ['MaterialsDEM.json', 'ProjectParametersDEM.json', 'inletPGDEM_FEM_boundary.mdpa', 'show_packing.py']
        for seed_file_name in seed_file_name_list:
            seed_file_path_and_name = os.path.join(os.getcwd(), seed_file_name)
            aim_file_path_and_name = os.path.join(aim_path, seed_file_name)

            if seed_file_name == 'ProjectParametersDEM.json':
                with open(seed_file_path_and_name, "r") as f_material:
                    with open(aim_file_path_and_name, "w") as f_material_w:
                        for line in f_material.readlines():
                            if "BoundingBoxMaxX" in line:
                                line = "    \"BoundingBoxMaxX\"                : " + str(self.BoundingBoxMaxX_update) + ', \n'
                            elif "\"BoundingBoxMaxY\"" in line:
                                line = "    \"BoundingBoxMaxY\"                : " + str(self.BoundingBoxMaxY_update) + ', \n'
                            elif "BoundingBoxMaxZ" in line:
                                line = "    \"BoundingBoxMaxZ\"                : " + str(self.BoundingBoxMaxZ_update) + ', \n'
                            elif "BoundingBoxMinX" in line:
                                line = "    \"BoundingBoxMinX\"                : " + str(self.BoundingBoxMinX_update) + ', \n'
                            elif "\"BoundingBoxMinY\"" in line:
                                line = "    \"BoundingBoxMinY\"                : " + str(self.BoundingBoxMinY_update) + ', \n'
                            elif "BoundingBoxMinZ" in line:
                                line = "    \"BoundingBoxMinZ\"                : " + str(self.BoundingBoxMinZ_update) + ', \n'
                            elif "FinalTime" in line:
                                line = "    \"FinalTime\"                      : " + str(self.dt * 2) + ', \n'
                            elif "\"GraphExportFreq\"" in line:
                                line = "    \"GraphExportFreq\"                : " + str(self.dt) + ', \n'
                            elif "VelTrapGraphExportFreq" in line:
                                line = "    \"VelTrapGraphExportFreq\"         : " + str(self.dt) + ', \n'
                            elif "OutputTimeStep" in line:
                                line = "    \"OutputTimeStep\"                 : " + str(self.dt) + ', \n'
                            f_material_w.write(line)
            else:
                if os.path.exists(seed_file_path_and_name):
                    shutil.copyfile(seed_file_path_and_name, aim_file_path_and_name)

    def copy_files_and_run_show_results(self):

        self.copy_seed_files_to_aim_folders()

        current_path = os.getcwd()
        aim_path = os.path.join(current_path,'show_packing')
        os.chdir(aim_path)
        if os.name == 'nt': # for windows
            os.system("python show_packing.py")
        else: # for linux
            os.system("python3 show_packing.py")
        os.chdir(current_path)

    def SetSecondStageFlag(self):

        self.second_stage_flag = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-parameters", required=True)
    arguments = parser.parse_args()
    case_parameters = load_case_parameters(arguments.case_parameters)

    Logger.GetDefaultOutput().SetSeverity(Logger.Severity.INFO)
    radius_multiplier = 1.0
    NormalizedKineticEnergy = 1e8
    Initial_radius_scaling_factor = 0.5
    max_radius_multiplier = 1.0 / Initial_radius_scaling_factor

    shutil.copyfile('inletPGDEM_ini.mdpa', 'inletPGDEM.mdpa')

    initial_packing = ParticlePacking.from_mdpa('inletPGDEM_ini.mdpa')

    while radius_multiplier < (max_radius_multiplier + 0.2):
        if os.path.exists('inletPG_Post_Files'):
            shutil.rmtree('inletPG_Post_Files', ignore_errors=True)
        with open("ProjectParametersDEM.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())

        global_model = KratosMultiphysics.Model()
        MyDemCase = DEMAnalysisStageWithFlush(global_model, parameters, radius_multiplier, initial_packing, case_parameters)
        MyDemCase.Initialize()
        MyDemCase.RunSolutionLoop()
        NormalizedKineticEnergy = MyDemCase.PassNormalizedKineticEnergy()
        MyDemCase.Finalize()
        print(' ')
        print("----------------------------Loop {} finished!".format(radius_multiplier))
        print(' ')
        radius_multiplier += 0.2
        radius_multiplier = round(radius_multiplier, 1)

    radius_multiplier = max_radius_multiplier

    if os.path.exists('inletPG_Post_Files'):
        shutil.rmtree('inletPG_Post_Files', ignore_errors=True)
    with open("ProjectParametersDEM.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    parameters["FinalTime"].SetDouble(10)
    global_model = KratosMultiphysics.Model()
    MyDemCase = DEMAnalysisStageWithFlush(global_model, parameters, radius_multiplier, initial_packing, case_parameters)
    MyDemCase.Initialize()
    MyDemCase.SetResetStart()
    MyDemCase.RunSolutionLoop()
    MyDemCase.Finalize()
