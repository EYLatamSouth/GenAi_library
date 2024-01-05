
import logging
import azureml.core
from azureml.core import Dataset
from azureml.core import Workspace
from azureml.core import Experiment
from azureml.data.datapath import DataPath
from azureml.pipeline.core import Pipeline
from azureml.pipeline.steps import PythonScriptStep
from logger import SetUpLogging

# Init logger
SetUpLogging().setup_logging()

# Parameters
project_name = 'GPT'
dataset_update = False
dataset_path = './samples/' + project_name + '/'
compute_cluster_update = False
compute_cluster_name = 'compute-cluster'
compute_cluster_size = 'STANDARD_DS11_V2'
environment_update = False
environment_name = 'vision_env'
environment_file = 'environment.yml'
publish_pipeline = False

# Load the workspace from the saved config file
ws = Workspace.from_config('./src/EYAnalytics/config/')

logging.info('Ready to use Azure ML {} to work with {}'.format(
    azureml.core.VERSION, ws.name))

# Get default datastore
datastore = ws.get_default_datastore()

# Set project path
pipeline_name = 'Inferencia ' + project_name


@SetUpLogging.function_logger
def register_dataset(name: str, target: str, description: str, tags: dict, type: str):

    if name not in ws.datasets or dataset_update is True:
        if type == 'TabularFile':
            # Create a tabular dataset from the path on the datastore (this may take a short while)
            dataset = Dataset.Tabular.from_delimited_files(
                path=(datastore, target))

        if type == 'Folder':
            # Upload directory to datastore
            dataset = Dataset.File.upload_directory(src_dir=dataset_path,
                                                    target=DataPath(
                                                        datastore, target),
                                                    overwrite=False,
                                                    show_progress=True)

        # Register the dataset
        dataset.register(workspace=ws,
                         name=name,
                         description=description,
                         tags=tags,
                         create_new_version=True)

        logging.info('New dataset registered.')

    else:
        logging.info('Dataset already registered.')

    # Return the dataset
    dataset = ws.datasets.get(name)

    return dataset


@SetUpLogging.function_logger
def register_cluster(compute_name='compute-cluster',
                     compute_size='STANDARD_DS11_V2',
                     min_nodes=0,
                     max_nodes=2):

    from azureml.core.compute import ComputeTarget, AmlCompute
    from azureml.core.compute_target import ComputeTargetException

    if compute_name not in ws.compute_targets or compute_cluster_update is True:

        try:
            # If it doesn't exist, create it
            compute_config = AmlCompute.provisioning_configuration(vm_size=compute_size,
                                                                   min_nodes=min_nodes,
                                                                   max_nodes=max_nodes,
                                                                   identity_type='SystemAssigned')
            compute_target = ComputeTarget.create(
                ws, compute_name, compute_config)
            compute_target.wait_for_completion(
                show_output=True, timeout_in_minutes=20)

            logging.info('New cluster registered.')

        except ComputeTargetException as message:
            logging.exception(message)

    else:
        # Check for existing compute target
        compute_target = ComputeTarget(workspace=ws, name=compute_name)

        logging.info('Cluster already registered.')

    return compute_target


@SetUpLogging.function_logger
def register_environment(environment_name: str, environment_file='environment.yml'):

    from azureml.core import Environment

    if environment_name not in ws.environments or environment_update is True:

        # Create a Python environment for the experiment (from a .yml file)
        environment = Environment.from_conda_specification(
            environment_name, environment_file)

        # Register the environment
        environment.register(workspace=ws)

        logging.info('New environment registered.')

    else:
        logging.info('Environment already registered.')

    environment = Environment.get(ws, environment_name)

    return environment


@SetUpLogging.function_logger
def set_runconfig(compute_target, environment):

    from azureml.core.runconfig import RunConfiguration

    # Create a new runconfig object for the pipeline
    run_config = RunConfiguration()

    # Configure runconfig object for the pipeline.
    run_config.target = compute_target
    run_config.environment = environment

    logging.info('Run configuration created.')

    return run_config


@SetUpLogging.function_logger
def build_pipeline(pipeline_name, input_data, output_data, compute_target, runconfig):

    # Step 1, Run the data prep script
    main_step = PythonScriptStep(name=pipeline_name,
                                 source_directory='./src/',
                                 script_name='main.py',
                                 arguments=['--input', input_data.as_named_input('input_data'),
                                            '--output', output_data],
                                 outputs=[output_data],
                                 compute_target=compute_target,
                                 runconfig=runconfig,
                                 allow_reuse=False)
    logging.info('Pipeline steps defined')

    # Construct the pipeline
    pipeline_steps = [main_step]
    pipeline = Pipeline(workspace=ws, steps=pipeline_steps)

    logging.info('Pipeline is built.')

    return pipeline


@SetUpLogging.function_logger
def main():

    # Create an experiment
    experiment = Experiment(workspace=ws, name=project_name)

    # Check and register Dataset
    input_data = None

    # Create an OutputFileDatasetConfig (temporary Data Reference)
    output_data = None

    # Check and register cluster
    compute_target = register_cluster(
        compute_cluster_name, compute_cluster_size)

    # Check and register environment
    environment = register_environment(environment_name, environment_file)

    # Configure pipeline runtime
    runconfig = set_runconfig(compute_target, environment)

    # Create a pipeline
    pipeline = build_pipeline(pipeline_name=pipeline_name,
                              input_data=input_data,
                              output_data=output_data,
                              compute_target=compute_target,
                              runconfig=runconfig)

    # Submite and run the pipeline
    pipeline_run = experiment.submit(pipeline, regenerate_outputs=True)
    logging.info('Pipeline submitted for execution.')

    # Wait for pipeline completion
    pipeline_run.wait_for_completion()
    logging.info('Pipeline completed.')

    # Publish the pipeline from the run
    if publish_pipeline is True:
        pipeline_run.publish_pipeline(name=pipeline_name,
                                      description='Inferece model',
                                      version='1.0')
        logging.info('Pipeline Published.')


if __name__ == "__main__":
    main()
