# House Price Prediction Pipeline

This project aims to understand how multiple frameworks like Pydantic, Daft, Ray Object Store, Ray Serve, and Temporal work both individually and in combination. The system implements a complete machine learning pipeline using by Temporal, with distributed processing and serving handled by Ray.

## Overview

The pipeline performs the following steps:

1. The input dataset is stored in Ray's global object store so that all Ray actors can access it without transferring large data between processes.
2. The feature inputs provided for prediction are validated using Pydantic models.
3. Data preprocessing is performed using Daft, allowing distributed and scalable transformations.
4. A Random Forest regressor is trained using the preprocessed dataset. The trained model is serialized and stored in the Ray object store, returning a model key referencing the stored object.
5. Ray Serve uses this model key to deploy a prediction endpoint. This endpoint provides an HTTP interface for sending prediction requests.
6. A final validation step confirms that the Ray Serve endpoint is operational and producing prediction responses correctly.

The entire workflow is implemented in `ml_pipeline_workflow.py`.

## Temporal Integration

The Temporal worker defines the pipeline logic, the activities involved, and execution constraints such as concurrency limits. The worker executes the steps in sequence and manages retries, and timeouts.

A separate client triggers the workflow by sending a request to Temporal. This client does not contain computation logic; it simply initiates and monitors the pipeline execution handled by the worker.

## Intsallation and Setup
First run `pip install -r requirements.txt`. Then make sure following frameworks are setup and started properly.
1. **Temporal**  
   Download the latest Temporal CLI release from:  

   https://github.com/temporalio/cli/releases  
   
   Extract the binary, move it to Program Files for global access, and add the folder to your system's PATH environment variable.  
   
   After setup, start a local Temporal server using: `temporal server start-dev`

2. **Ray**  
    Install Ray using: `pip install ray[default]`

    Keep in mind that ray multicluster setup is not supported by windows for now. 
    
    Start the Ray server using the command `ray start --head` and ray serve using `serve start`

3. **Run the Temporal Worker**  
    From the project root directory: `python -m temporal.worker`

4. **Run the Temporal Client**  
    From the project root directory:  `python -m temporal.client`

## Example Output of Temporal workflow
![alt text](<output.png>)

## Summary

This project demonstrates a distributed machine learning workflow that incorporates data validation, distributed preprocessing, model training, model serving, and workflow orchestration. Each framework plays a distinct role, and Temporal coordinates the end-to-end process in a reliable and scalable manner.
