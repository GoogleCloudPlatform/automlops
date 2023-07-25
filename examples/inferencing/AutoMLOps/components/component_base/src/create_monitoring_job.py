# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# DISCLAIMER: This code is generated as part of the AutoMLOps output.

import argparse
import json
from kfp.v2.components import executor

import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import *
from typing import *

def create_monitoring_job(
    alert_emails: list,
    cnt_user_engagement_threshold_value: float,
    country_threshold_value: float,
    data_source: str,
    log_sampling_rate: float,
    monitor_interval: int,
    project_id: str,
    region: str,
    target: str
):
    """Custom component that uploads a saved model from GCS to Vertex Model Registry
       and deploys the model to an endpoint for online prediction. Runs a prediction
       and explanation test as well.

    Args:
        alert_emails: List of emails to send monitoring alerts.
        cnt_user_engagement_threshold_value: Threshold value for the cnt_user_engagement feature.
        country_threshold_value: Threshold value for the country feature.
        data_source: BQ training data table.        
        log_sampling_rate: Sampling rate.
        monitor_interval: Monitoring interval in hours.
        project_id: Project_id.
        region: Region.
        target: Prediction target column name in training dataset.
    """
    from google.cloud import aiplatform
    from google.cloud.aiplatform import model_monitoring

    aiplatform.init(project=project_id, location=region)

    JOB_NAME = 'churn'
    SKEW_THRESHOLDS = {
        "country": country_threshold_value,
        "cnt_user_engagement": cnt_user_engagement_threshold_value,
    }
    DRIFT_THRESHOLDS = {
        "country": country_threshold_value,
        "cnt_user_engagement": cnt_user_engagement_threshold_value,
    }
    ATTRIB_SKEW_THRESHOLDS = {
        "country": country_threshold_value,
        "cnt_user_engagement": cnt_user_engagement_threshold_value,
    }
    ATTRIB_DRIFT_THRESHOLDS = {
        "country": country_threshold_value,
        "cnt_user_engagement": cnt_user_engagement_threshold_value,
    }

    skew_config = model_monitoring.SkewDetectionConfig(
        data_source=data_source,
        skew_thresholds=SKEW_THRESHOLDS,
        attribute_skew_thresholds=ATTRIB_SKEW_THRESHOLDS,
        target_field=target,
    )

    drift_config = model_monitoring.DriftDetectionConfig(
        drift_thresholds=DRIFT_THRESHOLDS,
        attribute_drift_thresholds=ATTRIB_DRIFT_THRESHOLDS,
    )

    explanation_config = model_monitoring.ExplanationConfig()
    objective_config = model_monitoring.ObjectiveConfig(
        skew_config, drift_config, explanation_config
    )

    # Create sampling configuration
    random_sampling = model_monitoring.RandomSampleConfig(sample_rate=log_sampling_rate)

    # Create schedule configuration
    schedule_config = model_monitoring.ScheduleConfig(monitor_interval=monitor_interval)

    # Create alerting configuration.
    alerting_config = model_monitoring.EmailAlertConfig(
        user_emails=alert_emails, enable_logging=True
    )

    # Create the monitoring job.
    job = aiplatform.ModelDeploymentMonitoringJob.create(
        display_name=JOB_NAME,
        logging_sampling_strategy=random_sampling,
        schedule_config=schedule_config,
        alert_config=alerting_config,
        objective_configs=objective_config,
        project=project_id,
        location=region,
        endpoint=endpoint,
    )

def main():
    """Main executor."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--executor_input', type=str)
    parser.add_argument('--function_to_execute', type=str)

    args, _ = parser.parse_known_args()
    executor_input = json.loads(args.executor_input)
    function_to_execute = globals()[args.function_to_execute]

    executor.Executor(
        executor_input=executor_input,
        function_to_execute=function_to_execute).execute()

if __name__ == '__main__':
    main()
