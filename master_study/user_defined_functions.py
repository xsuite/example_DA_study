def generate_run_sh(node, generation_number):
   python_command =  (node
                     .root
                     .parameters["generations"]
                     [generation_number]
                     ["job_executable"])
   return (f'source {node.root.parameters["setup_env_script"]}\n'
           f'cd {node.get_abs_path()}\n'
           f'python {python_command} > output.txt 2> error.txt\n')

def generate_run_sh_htc(node, generation_number):
   python_command =  (node
                     .root
                     .parameters["generations"]
                     [generation_number]
                     ["job_executable"])
   return (f'#!/bin/bash\n'
           f'source {node.root.parameters["setup_env_script"]}\n'
           f'cd {node.get_abs_path()}\n'
           f'python {python_command} > output.txt 2> error.txt\n'
           f'rm -rf modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at*\n')
