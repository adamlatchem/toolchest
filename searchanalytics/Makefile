ACTIVATE := . venv/bin/activate
ECHO     := echo
EXEC     := exec
PIP      :=  venv/bin/pip3
PYTHON0  := /usr/bin/python3
PYTHON   := venv/bin/python3

help:
	# Search Analytics
	# ---------------------------------------
	# Goals:
	#   venv     : build appropriate virtual env
	#   activate : activate virtual env in new shell - to deactivate type exit
	# ---------------------------------------

venv:
	$(PYTHON0) -m venv venv
	$(ACTIVATE) && \
		$(PIP) install --upgrade pip && \
		$(PIP) install -r pipDependencies

activate:	venv
	$(ACTIVATE) && \
		$(ECHO) '*** Type exit to deactivate venv ***' && \
		$(EXEC) /bin/bash

.PHONY:	activate
