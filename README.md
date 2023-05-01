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
```bash
python -m imageassessmentservice.server
```
and after activating the environment for the client, run
```bash
python -m imageassessmentservice.client images_source_folder ratings_target_file_path server_address
```
Here, `images_source_folder` is the folder containing the images to assess, `ratings_target_file_path` will contain the
ratings for all images and `server_address` is the IP address of the assessment server.

## Notes
Please keep the following aspects in mind when using this code:
* Images are assessed relative to each other -- the assessment results may be better when assessing larger amounts of images
* Data is (currently) transferred without encryption