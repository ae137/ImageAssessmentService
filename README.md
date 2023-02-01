# ImageAssessmentService
Implementing a service that provides aesthetic and technical image assessment

## Setup
### Install dependences
The dependences of `imageassessmentservice` are listed in `requirements.txt`.

### Generating protobuf files
Generating code from the protobuf files is easiest when installing the package from the checked out git repository.
After cloning the repository, run the following command from the root folder of the project
```bash
python -m grpc_tools.protoc -I protobufs --python_out=imageassessmentservice --grpc_python_out=imageassessmentservice protobufs/imageassessment.proto
```
Subsequently, the package including the generated code can be installed via
```bash
pip install .
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