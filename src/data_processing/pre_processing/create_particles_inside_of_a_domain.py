#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "0.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "August 2, 2023"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

import json
import random
import shutil
import math
from KratosMultiphysics import *
from KratosMultiphysics.DEMApplication import *
from data_processing.pre_processing.particle_case_request import (
    ParticleCaseRequest,
    ParticleGenerationContext,
)

class CreateParticlesInsideOfADomain():

    def __init__(self, context: ParticleGenerationContext) -> None:

        self.context = context
        self.generated_cases_path = self.context.run_dir / "generated_cases"
        self.clear_old_cases_folder()

    def create_case(self, request: ParticleCaseRequest):
        self.Initialize(request)
        self.CreateParticles()
        self.WriteOutGIDData(request.output_file_name)

    def Initialize(self, request: ParticleCaseRequest):
        self.particle_list = []
        self.particle_list_side = []

        parameters = self.context.parameters
        self.rve_size = [
            parameters["domain_length_x"],
            parameters["domain_length_y"],
            parameters["domain_length_z"],
        ]
        domain_scale_multiplier = parameters[
            "random_particle_generation_parameters"
        ]["domain_scale_multiplier"]
        half_sizes = [
            0.5 * domain_scale_multiplier * length
            for length in self.rve_size
        ]
        self.x_min, self.y_min, self.z_min = [-size for size in half_sizes]
        self.x_max, self.y_max, self.z_max = half_sizes

        self.parameters_all = Parameters(json.dumps(parameters))
        self.parameters = self.parameters_all["random_particle_generation_parameters"]
        self.initial_target_packing_density = self.parameters["target_packing_density"].GetDouble()
        self.tolerance_of_packing_density = self.parameters["tolerance_of_packing_density"].GetDouble()
        self.tolerance_of_unbalanced_force = self.parameters["tolerance_of_unbalanced_force"].GetDouble()
        self.tolerance_of_target_mean_stress = self.parameters["tolerance_of_target_mean_stress"].GetDouble()
        self.minimum_mean_stress = self.parameters["minimum_mean_stress"].GetDouble()
        if request.packing_density is not None:
            self.parameters["target_packing_density"].SetDouble(request.packing_density)
        print("try_packing_density = {}".format(request.packing_density))
        print("target_packing_density = {}".format(self.parameters["target_packing_density"].GetDouble()))
        random_settings = self.parameters["random_variable_settings"]
        radius_scale_multiplier = random_settings["radius_scale_multiplier"].GetDouble()
        original_psd = random_settings["possible_values"].GetVector()
        scaled_psd = [radius * radius_scale_multiplier for radius in original_psd]
        random_settings["possible_values"].SetVector(scaled_psd)

        self.case_number = request.case_number
        self.case_path = self.generated_cases_path / f"case_{request.case_number}"

        self.create_new_cases_folder()
        self.write_case_parameters()
        self.copy_seed_files_to_aim_folders()

    def write_case_parameters(self):
        case_parameters = {
            "attempt_packing_density": self.parameters["target_packing_density"].GetDouble(),
            "servo_target_packing_density": self.initial_target_packing_density,
            "domain_scale_multiplier": self.parameters["domain_scale_multiplier"].GetDouble(),
            "tolerance_of_packing_density": self.tolerance_of_packing_density,
            "tolerance_of_unbalanced_force": self.tolerance_of_unbalanced_force,
            "tolerance_of_target_mean_stress": self.tolerance_of_target_mean_stress,
            "minimum_mean_stress": self.minimum_mean_stress,
        }
        parameters_path = self.case_path / "demgen_case_parameters.json"
        with parameters_path.open("w", encoding="utf-8") as parameters_file:
            json.dump(case_parameters, parameters_file, indent=2)

    def clear_old_cases_folder(self):

        if self.generated_cases_path.exists():
            shutil.rmtree(self.generated_cases_path, ignore_errors=True)
        self.generated_cases_path.mkdir(parents=True, exist_ok=True)

    def create_new_cases_folder(self):

        if self.case_path.exists():
            shutil.rmtree(self.case_path, ignore_errors=True)
        self.case_path.mkdir(parents=True, exist_ok=True)

    def copy_seed_files_to_aim_folders(self):

        seed_file_name_list = ['MaterialsDEM.json', 'ProjectParametersDEM.json']
        for seed_file_name in seed_file_name_list:
            seed_file_path_and_name = self.context.run_dir / seed_file_name
            aim_file_path_and_name = self.case_path / seed_file_name
            shutil.copyfile(seed_file_path_and_name, aim_file_path_and_name)

        if self.parameters_all["generator_name"].GetString() == "isotropic_compression_method":
            seed_file_name_list = ['inletPGDEM_FEM_boundary.mdpa']
            for seed_file_name in seed_file_name_list:
                seed_file_path_and_name = self.context.project_root / 'src' / 'utilities' / 'rem_seed_files' / seed_file_name
                aim_file_path_and_name = self.case_path / seed_file_name
                shutil.copyfile(seed_file_path_and_name, aim_file_path_and_name)

        seed_file_path_and_name = self.context.project_root / 'src' / 'utilities' / 'show_packing.py'
        aim_file_path_and_name = self.case_path / 'show_packing.py'
        shutil.copyfile(seed_file_path_and_name, aim_file_path_and_name)

    def CreateParticles(self):

        is_first_particle = True
        particle_cnt = 1
        particle_volume = 0
        #aim_particle_number = self.parameters["aim_particle_number"].GetInt()
        target_packing_density = self.parameters["target_packing_density"].GetDouble()
        print("target_packing_density = {}".format(target_packing_density))
        radius_scale_multiplier = self.parameters["random_variable_settings"]["radius_scale_multiplier"].GetDouble()
        aim_volume = self.rve_size[0] * self.rve_size[1] * self.rve_size[2] * target_packing_density * (radius_scale_multiplier ** 3)

        seed = self.parameters["SEED"].GetInt()
        if "DO_USE_SEED" in self.parameters.keys():
            if self.parameters["DO_USE_SEED"].GetBool():
                random.seed(seed)
        else:
            print("DO_USE_SEED is not specified in the ParametersDEMGen.json file, so the random seed will not be used.")

        creator_destructor = ParticleCreatorDestructor()
        self.Fast_Filling_Creator = Fast_Filling_Creator(self.parameters, seed)

        check_intial_overlap_option = False
        if "check_initial_overlap_option" in self.parameters.keys():
            check_intial_overlap_option = self.parameters["check_initial_overlap_option"].GetBool()
            if check_intial_overlap_option:
                print("Check_initial_overlap_option is set to True, so the particles will be checked for overlap during generation.")

        while particle_volume < aim_volume:

            p_parameters_dict = {
                    "id" : 0,
                    "p_x" : 0.0,
                    "p_y" : 0.0,
                    "p_z" : 0.0,
                    "radius" : 0.0,
                    "p_v_x" : 0.0,
                    "p_v_y" : 0.0,
                    "p_v_z" : 0.0,
                    "p_ele_id": 0,
                    "p_group_id": 0
                    }

            r = self.Fast_Filling_Creator.GetRandomParticleRadius(creator_destructor)
            radius_max = self.parameters["MAXIMUM_RADIUS"].GetDouble() * self.parameters["random_variable_settings"]["radius_scale_multiplier"].GetDouble()

            if check_intial_overlap_option:
                if is_first_particle:
                    if self.parameters_all["periodic_boundary_option"].GetBool():
                        x = random.uniform(self.x_min , self.x_max)
                        y = random.uniform(self.y_min , self.y_max)
                        z = random.uniform(self.z_min , self.z_max)
                    else:
                        x = random.uniform(self.x_min + radius_max, self.x_max - radius_max)
                        y = random.uniform(self.y_min + radius_max, self.y_max - radius_max)
                        z = random.uniform(self.z_min + radius_max, self.z_max - radius_max)
                    p_parameters_dict["id"] = particle_cnt
                    p_parameters_dict["p_x"] = x
                    p_parameters_dict["p_y"] = y
                    p_parameters_dict["p_z"] = z
                    p_parameters_dict["radius"] = r
                    p_parameters_dict["p_ele_id"] = particle_cnt
                    self.particle_list.append(p_parameters_dict)
                    print("Added particle number = {}".format(particle_cnt))
                    particle_cnt += 1
                    particle_volume += 4/3 * math.pi * (r**3)
                    is_first_particle = False
                else:
                    IsOverlaped = True
                    loop_cnt = 0
                    while IsOverlaped:
                        if self.parameters_all["periodic_boundary_option"].GetBool():
                            self.x = random.uniform(self.x_min, self.x_max)
                            self.y = random.uniform(self.y_min, self.y_max)
                            self.z = random.uniform(self.z_min, self.z_max)
                            for particle in self.particle_list:
                                IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, self.z, r, particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"])
                                if IsOverlaped:
                                    break

                            real_RVE_x_length = self.x_max - self.x_min
                            real_RVE_y_length = self.y_max - self.y_min
                            real_RVE_z_length = self.z_max - self.z_min

                            x_plus = self.x + real_RVE_x_length
                            x_minus = self.x - real_RVE_x_length
                            y_plus = self.y + real_RVE_y_length
                            y_minus = self.y - real_RVE_y_length
                            z_plus = self.z + real_RVE_z_length
                            z_minus = self.z - real_RVE_z_length

                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, self.y, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, y_plus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, y_minus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, self.y, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, self.y, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, self.y, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, y_plus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, y_minus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, self.y, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, self.y, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break

                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_minus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, y_minus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, y_minus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_minus, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_minus, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_plus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, y_plus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, y_plus, self.z, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_plus, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_plus, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break

                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, self.y, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, self.y, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_plus, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_minus, z_plus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                            if not IsOverlaped:
                                for particle in self.particle_list_side:
                                    p_x, p_y, p_z, p_r = particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"]
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_minus, self.y, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(x_plus, self.y, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_plus, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                                    IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, y_minus, z_minus, r, p_x, p_y, p_z, p_r)
                                    if IsOverlaped:
                                        break
                        else:
                            self.x = random.uniform(self.x_min + radius_max, self.x_max - radius_max)
                            self.y = random.uniform(self.y_min + radius_max, self.y_max - radius_max)
                            self.z = random.uniform(self.z_min + radius_max, self.z_max - radius_max)
                            for particle in self.particle_list:
                                IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, self.z, r, particle["p_x"], particle["p_y"], particle["p_z"], particle["radius"])
                                if IsOverlaped:
                                    break
                        loop_cnt += 1
                        if loop_cnt > 10000:
                            print("Too much loop for one particle!")
                            exit(0)

                    p_parameters_dict["id"] = particle_cnt
                    p_parameters_dict["p_x"] = self.x
                    p_parameters_dict["p_y"] = self.y
                    p_parameters_dict["p_z"] = self.z
                    p_parameters_dict["radius"] = r
                    p_parameters_dict["p_ele_id"] = particle_cnt
                    self.particle_list.append(p_parameters_dict)
                    if self.parameters_all["periodic_boundary_option"].GetBool():
                        if self.x <= self.x_min + radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                        elif self.x >= self.x_max - radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                        elif self.y <= self.y_min + radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                        elif self.y >= self.y_max - radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                        elif self.z <= self.z_min + radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                        elif self.z >= self.z_max - radius_max * 2:
                            self.particle_list_side.append(p_parameters_dict)
                    print("Added particle number = {}".format(particle_cnt))
                    particle_cnt += 1
                    particle_volume += 4/3 * math.pi * (r**3)

            else: # if not check_intial_overlap_option

                if self.parameters_all["periodic_boundary_option"].GetBool():
                    x = random.uniform(self.x_min , self.x_max)
                    y = random.uniform(self.y_min , self.y_max)
                    z = random.uniform(self.z_min , self.z_max)
                else:
                    x = random.uniform(self.x_min + radius_max, self.x_max - radius_max)
                    y = random.uniform(self.y_min + radius_max, self.y_max - radius_max)
                    z = random.uniform(self.z_min + radius_max, self.z_max - radius_max)

                p_parameters_dict["id"] = particle_cnt
                p_parameters_dict["p_x"] = x
                p_parameters_dict["p_y"] = y
                p_parameters_dict["p_z"] = z
                p_parameters_dict["radius"] = r
                p_parameters_dict["p_ele_id"] = particle_cnt
                self.particle_list.append(p_parameters_dict)
                print("Added particle number = {}".format(particle_cnt))
                particle_cnt += 1
                particle_volume += 4/3 * math.pi * (r**3)

    def WriteOutGIDData(self, aim_file_name):

        aim_path_and_name = self.case_path / aim_file_name

        with aim_path_and_name.open('w') as f:
            # write the particle information
            f.write("Begin ModelPartData \n //  VARIABLE_NAME value \n End ModelPartData \n \n Begin Properties 0 \n End Properties \n \n")
            f.write("Begin Nodes\n")
            for p_pram_dict in self.particle_list:
                f.write(str(p_pram_dict["id"]) + ' ' + str(p_pram_dict["p_x"]) + ' ' + str(p_pram_dict["p_y"]) + ' ' + str(p_pram_dict["p_z"]) + '\n')
            f.write("End Nodes \n \n")

            f.write("Begin Elements SphericParticle3D// GUI group identifier: Body \n")
            for p_pram_dict in self.particle_list:
                f.write(str(p_pram_dict["p_ele_id"]) + ' ' + ' 0 ' + str(p_pram_dict["id"]) + '\n')
            f.write("End Elements \n \n")

            f.write("Begin NodalData RADIUS // GUI group identifier: Body \n")
            for p_pram_dict in self.particle_list:
                f.write(str(p_pram_dict["id"]) + ' ' + ' 0 ' + str(p_pram_dict["radius"]) + '\n')
            f.write("End NodalData \n \n")

            ''' only works for continuum DEM calculation
            f.write("Begin NodalData COHESIVE_GROUP // GUI group identifier: Body \n")
            for p_pram_dict in self.p_pram_list:
                f.write(str(p_pram_dict["id"]) + ' ' + ' 0 ' + " 1 " + '\n')
            f.write("End NodalData \n \n")

            f.write("Begin NodalData SKIN_SPHERE \n End NodalData \n \n")
            '''

            f.write("Begin SubModelPart DEMParts_Body // Group Body // Subtree DEMParts \n Begin SubModelPartNodes \n")
            for p_pram_dict in self.particle_list:
                if p_pram_dict["p_group_id"] == 0:
                    f.write(str(p_pram_dict["id"]) + '\n')
            f.write("End SubModelPartNodes \n Begin SubModelPartElements \n ")
            for p_pram_dict in self.particle_list:
                if p_pram_dict["p_group_id"] == 0:
                    f.write(str(p_pram_dict["p_ele_id"]) + '\n')
            f.write("End SubModelPartElements \n")
            f.write("Begin SubModelPartConditions \n End SubModelPartConditions \n End SubModelPart \n \n")

            #write out joint group
            joint_exist = False
            for p_pram_dict in self.particle_list:
                if p_pram_dict["p_group_id"] == 1:
                    joint_exist = True

            if joint_exist:
                f.write("Begin SubModelPart DEMParts_Joint // Group Joint // Subtree DEMParts \n Begin SubModelPartNodes \n")
                for p_pram_dict in self.particle_list:
                    if p_pram_dict["p_group_id"] == 1:
                        f.write(str(p_pram_dict["id"]) + '\n')
                f.write("End SubModelPartNodes \n Begin SubModelPartElements \n ")
                for p_pram_dict in self.particle_list:
                    if p_pram_dict["p_group_id"] == 1:
                        f.write(str(p_pram_dict["p_ele_id"]) + '\n')
                f.write("End SubModelPartElements \n")
                f.write("Begin SubModelPartConditions \n End SubModelPartConditions \n End SubModelPart \n")

        print("Successfully write out file case_{}-{}!".format(self.case_number, aim_file_name))
