# ImageAssessmentService
Implementing a service that provides aesthetic and technical image assessment

## Setup
### Install dependences
Image assessment client and service can be run in different conda environments. In the environment for the client,
the dependences can be installed from `requirements-client.txt`. In the environment for the service, the dependences
can be installed from `requirements.txt`.

### Generating protobuf files
In order to generate the protobuf files, run the following command (necessary for the client and the server) from
the root folder of the project.
```bash
python -m grpc_tools.protoc -I protobufs --python_out=imageassessmentservice --grpc_python_out=imageassessmentservice protobufs/imageassessment.proto
```

## Running the client and server
After activating the environment for the server, switch to folder `imageassessmentservice` and run
```python
python server.py
```
and after activating the enviornment for the client, run 
```python
python client.py images_source_folder images_target_folder server_address
```
Here, `images_source_folder` is the folder containing the images to assess, `images_target_folder` will contain the
assessed and sorted images and `server_address` is the IP address of the assessment server.

## Notes
Please keep the following aspects in mind when using this code:
* Images are assessed relative to each other -- the assessment results may be better when assessing larger amounts of images
* Data is (currently) transferred without encryption