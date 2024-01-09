"""Sends a PipelineJob to Vertex AI."""

import argparse
import logging
import os
import yaml

from google.cloud import aiplatform
from google.cloud.aiplatform import model_monitoring

logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)


def create_or_update_monitoring_job(
    alert_emails: list,
    automatic_retrain: bool,
    drift_thresholds: dict,
    job_display_name: str,
    model_endpoint: str,
    monitoring_interval: int,
    monitoring_location: str,
    project_id: str,
    sample_rate: float,
    skew_thresholds: dict,
    target_field: str,
    training_dataset: str,
):
    """Creates or updates a model monitoring job on the given model.

    Args:
        alert_emails: Optional list of emails to send monitoring alerts.
            Email alerts not used if this value is set to None.
        automatic_retrain: Boolean that specifies whether to retrain the model if an alert is generated.
        drift_thresholds: TODO(@srastatter).
        job_display_name: Display name of the ModelDeploymentMonitoringJob. The name can be up to 128 characters 
            long and can be consist of any UTF-8 characters.
        model_endpoint: Endpoint resource name of the deployed model to monitoring.
            Format: projects/{project}/locations/{location}/endpoints/{endpoint}
        monitoring_interval: Configures model monitoring job scheduling interval in hours.
            This defines how often the monitoring jobs are triggered.
        monitoring_location: Location to retrieve ModelDeploymentMonitoringJob from.
        project_id: The project ID.
        sample_rate: Used for drift detection, specifies what percent of requests to the endpoint are randomly sampled
            for drift detection analysis. This value most range between (0, 1].
        skew_thresholds: TODO(@srastatter).
        target_field: Prediction target column name in training dataset.
        training_dataset: Training dataset used to train the deployed model. This field is required if
            using skew detection.
    """

    aiplatform.init(project=project_id, location=monitoring_location)

    # check if endpoint exists
    endpoint_resource_names = [e.resource_name for e in aiplatform.Endpoint.list()]
    if model_endpoint not in endpoint_resource_names:
        raise ValueError(f'Model endpoint {endpoint_resource_names} not found in {monitoring_location}')
    else:
        endpoint = aiplatform.Endpoint(model_endpoint)

    if not skew_thresholds and not drift_thresholds:
        raise ValueError('skew_thresolds and drift_thresholds cannot both be None.')

    # Set skew and drift thresholds
    if skew_thresholds:
        skew_config = model_monitoring.SkewDetectionConfig(
            data_source=training_dataset,
            skew_thresholds=skew_thresholds,
            target_field=target_field
        )

    if drift_thresholds:
        drift_config = model_monitoring.DriftDetectionConfig(
            drift_thresholds=drift_thresholds
        )

    objective_config = model_monitoring.ObjectiveConfig(
        skew_config, drift_config, explanation_config=None
    )

    # Create sampling configuration
    random_sampling = model_monitoring.RandomSampleConfig(sample_rate=sample_rate)

    # Create schedule configuration
    schedule_config = model_monitoring.ScheduleConfig(monitor_interval=monitoring_interval)

    # Create alerting configuration.
    if alert_emails:
        alerting_config = model_monitoring.EmailAlertConfig(
            user_emails=alert_emails, enable_logging=True
        )
    else:
        alerting_config = None
        # TODO set retraining stuff

    # check if job already exists
    monitoring_jobs = [mj.display_name for mj in aiplatform.ModelDeploymentMonitoringJob.list()]
    if job_display_name not in monitoring_jobs:
        # Create the monitoring job.
        job = aiplatform.ModelDeploymentMonitoringJob.create(
            display_name=job_display_name,
            logging_sampling_strategy=random_sampling,
            schedule_config=schedule_config,
            alert_config=alerting_config,
            objective_configs=objective_config,
            project=project_id,
            location=monitoring_location,
            endpoint=endpoint
        )
    else:
        # Update the monitoring job.
        job = aiplatform.ModelDeploymentMonitoringJob(job_display_name).update(
            display_name=job_display_name,
            logging_sampling_strategy=random_sampling,
            schedule_config=schedule_config,
            alert_config=alerting_config,
            objective_configs=objective_config
        )



def deploy_and_test_model(
    model_directory: str,
    project_id: str,
    region: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction. Runs a prediction
       and explanation test as well.

    Args:
        model_directory: GS location of saved model.
        project_id: Project_id.
        region: Region.
    """
    from google.cloud import aiplatform
    from google.cloud.aiplatform.explain.metadata.tf.v2 import \
    saved_model_metadata_builder
    import pprint as pp

    aiplatform.init(project=project_id, location=region)

    MODEL_NAME = 'churn'
    IMAGE = 'us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-5:latest'
    params = {'sampled_shapley_attribution': {'path_count': 10}}
    EXPLAIN_PARAMS = aiplatform.explain.ExplanationParameters(params)
    builder = saved_model_metadata_builder.SavedModelMetadataBuilder(
        model_path=model_directory, outputs_to_explain=['churned_probs']
    )
    EXPLAIN_META = builder.get_metadata_protobuf()
    DEFAULT_INPUT = {
        'cnt_ad_reward': 0,
        'cnt_challenge_a_friend': 0,
        'cnt_completed_5_levels': 1,
        'cnt_level_complete_quickplay': 3,
        'cnt_level_end_quickplay': 5,
        'cnt_level_reset_quickplay': 2,
        'cnt_level_start_quickplay': 6,
        'cnt_post_score': 34,
        'cnt_spend_virtual_currency': 0,
        'cnt_use_extra_steps': 0,
        'cnt_user_engagement': 120,
        'country': 'Denmark',
        'dayofweek': 3,
        'julianday': 254,
        'language': 'da-dk',
        'month': 9,
        'operating_system': 'IOS',
        'user_pseudo_id': '104B0770BAE16E8B53DF330C95881893',
    }

    model = aiplatform.Model.upload(
        display_name=MODEL_NAME,
        artifact_uri=model_directory,
        serving_container_image_uri=IMAGE,
        explanation_parameters=EXPLAIN_PARAMS,
        explanation_metadata=EXPLAIN_META,
        sync=True
    )

    endpoint = model.deploy(
        machine_type='n1-standard-4',
        deployed_model_display_name='deployed-churn-model')

    # Test predictions
    print('running prediction test...')
    try:
        resp = endpoint.predict([DEFAULT_INPUT])
        for i in resp.predictions:
            vals = i['churned_values']
            probs = i['churned_probs']
        for i in range(len(vals)):
            print(vals[i], probs[i])
        pp.pprint(resp)
    except Exception as ex:
        print('prediction request failed', ex)

    # Test explanations
    print('\nrunning explanation test...')
    try:
        features = []
        scores = []
        resp = endpoint.explain([DEFAULT_INPUT])
        for i in resp.explanations:
            for j in i.attributions:
                for k in j.feature_attributions:
                    features.append(k)
                    scores.append(j.feature_attributions[k])
        features = [x for _, x in sorted(zip(scores, features))]
        scores = sorted(scores)
        for i in range(len(scores)):
            print(scores[i], features[i])
        pp.pprint(resp)
    except Exception as ex:
        print('explanation request failed', ex)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                        help='The config file for setting monitoring values.')
    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    deploy_and_test_model(
        model_directory='gs://mco-mm/churn',
        project_id=config['gcp']['project_id'],
        region='us-central1'
    )

    # create_or_update_monitoring_job(
    #     alert_emails=config['monitoring']['alert_emails'],
    #     automatic_retrain=config['monitoring']['automatic_retrain'],
    #     drift_thresholds=config['monitoring']['drift_thresholds'],
    #     job_display_name=config['monitoring']['job_display_name'],
    #     model_endpoint=config['monitoring']['model_endpoint'],
    #     monitoring_interval=config['monitoring']['monitoring_interval'],
    #     monitoring_location=config['monitoring']['monitoring_location'],
    #     project_id=config['gcp']['project_id'],
    #     sample_rate=config['monitoring']['sample_rate'],
    #     skew_thresholds=config['monitoring']['skew_thresholds'],
    #     target_field=config['monitoring']['target_field'],
    #     training_dataset=config['monitoring']['training_dataset']
    # )
