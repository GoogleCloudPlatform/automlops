
@dsl.pipeline(name='training-pipeline')
def pipeline(bq_table: str,
             output_model_directory: str,
             project: str,
             region: str,
            ):

    dataset_task = create_dataset(
        bq_table=bq_table, 
        project=project)

    model_task = train_model(
        output_model_directory=output_model_directory,
        dataset=dataset_task.output)

    deploy_task = deploy_model(
        model=model_task.outputs["model"],
        project=project,
        region=region)
