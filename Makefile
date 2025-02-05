# Variables
PYTHON = python
PROTOC = $(PYTHON) -m grpc_tools.protoc
PROTO_DIR = protobufs
SRC_DIR = imageassessmentservice
GEN_DIR = $(SRC_DIR)/generated
BUILD_DIR = build
DIST_DIR = dist

# Default target
all: build

# Generate Protobuf files
generate:
	@mkdir -p $(GEN_DIR)
	@$(PROTOC) -I $(PROTO_DIR) --python_out=$(GEN_DIR) --grpc_python_out=$(GEN_DIR) $(PROTO_DIR)/*.proto
	@touch $(GEN_DIR)/__init__.py

# Clean generated files
clean:
	@rm -rf $(GEN_DIR)
	@rm -rf $(BUILD_DIR)
	@rm -rf $(DIST_DIR)
	@rm -rf imageassessmentservice.egg-info

# Build package
build: generate
	$(PYTHON) setup.py sdist bdist_wheel

# Install dependencies
install: build
	pip install .

deps:
	pip install -r requirements.txt

install-all: deps install
