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
from KratosMultiphysics import *
from KratosMultiphysics.DEMApplication import *
from data_processing.pre_processing.particle_case_request import (
    ParticleCaseRequest,
    ParticleGenerationContext,
)
from particles import ParticlePacking, SphericalParticle
from curve_generation import load_curve_generation_settings


class CreateParticlesInsideOfADomain():

    def __init__(self, context: ParticleGenerationContext) -> None:

        self.context = context
        self.generated_cases_path = self.context.run_dir / "generated_cases"
        self.clear_old_cases_folder()

    def create_case(self, request: ParticleCaseRequest):
        self.Initialize(request)
        particles = self.CreateParticles()
        particles.write_mdpa(self.case_path / request.output_file_name)
        print(
            "Successfully wrote file "
            f"case_{self.case_number}-{request.output_file_name}!"
        )

    def Initialize(self, request: ParticleCaseRequest):
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
        self.curve_generation = load_curve_generation_settings(
            parameters,
            self.context.run_dir / "ProjectParametersDEM.json",
        )
        self.initial_target_packing_density = self.curve_generation.initial_density
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
            "curve_generation": self.curve_generation.to_dict(),
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

    def CreateParticles(self) -> ParticlePacking:

        particles = ParticlePacking()
        side_particles: list[SphericalParticle] = []
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
                    particle = SphericalParticle(
                        node_id=particle_cnt,
                        element_id=particle_cnt,
                        position=(x, y, z),
                        radius=r,
                    )
                    particles.add(particle)
                    print("Added particle number = {}".format(particle_cnt))
                    particle_cnt += 1
                    particle_volume += particle.volume
                    is_first_particle = False
                else:
                    IsOverlaped = True
                    loop_cnt = 0
                    while IsOverlaped:
                        if self.parameters_all["periodic_boundary_option"].GetBool():
                            self.x = random.uniform(self.x_min, self.x_max)
                            self.y = random.uniform(self.y_min, self.y_max)
                            self.z = random.uniform(self.z_min, self.z_max)
                            for particle in particles:
                                p_x, p_y, p_z = particle.position
                                IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, self.z, r, p_x, p_y, p_z, particle.radius)
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                                for particle in side_particles:
                                    p_x, p_y, p_z = particle.position
                                    p_r = particle.radius
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
                            for particle in particles:
                                p_x, p_y, p_z = particle.position
                                IsOverlaped = self.Fast_Filling_Creator.CheckHasIndentationOrNot(self.x, self.y, self.z, r, p_x, p_y, p_z, particle.radius)
                                if IsOverlaped:
                                    break
                        loop_cnt += 1
                        if loop_cnt > 10000:
                            print("Too much loop for one particle!")
                            exit(0)

                    particle = SphericalParticle(
                        node_id=particle_cnt,
                        element_id=particle_cnt,
                        position=(self.x, self.y, self.z),
                        radius=r,
                    )
                    particles.add(particle)
                    if self.parameters_all["periodic_boundary_option"].GetBool():
                        if self.x <= self.x_min + radius_max * 2:
                            side_particles.append(particle)
                        elif self.x >= self.x_max - radius_max * 2:
                            side_particles.append(particle)
                        elif self.y <= self.y_min + radius_max * 2:
                            side_particles.append(particle)
                        elif self.y >= self.y_max - radius_max * 2:
                            side_particles.append(particle)
                        elif self.z <= self.z_min + radius_max * 2:
                            side_particles.append(particle)
                        elif self.z >= self.z_max - radius_max * 2:
                            side_particles.append(particle)
                    print("Added particle number = {}".format(particle_cnt))
                    particle_cnt += 1
                    particle_volume += particle.volume

            else: # if not check_intial_overlap_option

                if self.parameters_all["periodic_boundary_option"].GetBool():
                    x = random.uniform(self.x_min , self.x_max)
                    y = random.uniform(self.y_min , self.y_max)
                    z = random.uniform(self.z_min , self.z_max)
                else:
                    x = random.uniform(self.x_min + radius_max, self.x_max - radius_max)
                    y = random.uniform(self.y_min + radius_max, self.y_max - radius_max)
                    z = random.uniform(self.z_min + radius_max, self.z_max - radius_max)

                particle = SphericalParticle(
                    node_id=particle_cnt,
                    element_id=particle_cnt,
                    position=(x, y, z),
                    radius=r,
                )
                particles.add(particle)
                print("Added particle number = {}".format(particle_cnt))
                particle_cnt += 1
                particle_volume += particle.volume

        return particles
