#avec GNUmake dans le path
#define the name of the YAML file
YAML_file := env_co.yml

current_proxy := "http://165.225.204.22:80"
current_no_proxy:= ".myarcelormittal.com"

# default target, when make executed without arguments
all: update_env

create_env:
# check if the user is using a local windows install
ifeq ($(OS),Windows_NT)
	export http_proxy=$(current_proxy) && \
	export https_proxy=$(current_proxy) && \
	export no_proxy=$(current_no_proxy) && \
	conda env create -f $(YAML_file)
else
	conda env create -f $(YAML_file)
endif

update_env:
ifeq ($(OS),Windows_NT)
	export http_proxy=$(current_proxy) && \
	export https_proxy=$(current_proxy) && \
	export no_proxy=$(current_no_proxy) && \
	conda env update -f $(YAML_file)
else
	conda env update -f $(YAML_file)
endif

remove:
	conda env remove -n co_test

run:
	conda run -n co_test ---no-capture-output python main.py


.PHONY: all remove run create_env update_env docs
