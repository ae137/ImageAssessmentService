# ImageAssessmentService
Implementing a service that provides aesthetic and technical image assessment

## Generating protobuf files
python -m grpc_tools.protoc -I protobufs --python_out=imageassessmentservice --grpc_python_out=imageassessmentservice protobufs/imageassessment.proto