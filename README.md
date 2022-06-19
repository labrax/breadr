## breadr

Tested using Python 3.10 (Python 3.8 might work)

###### Roadmap

3.0

- Interpreter/language for crumbs

2.0

- R easy-handler
  - Create handlers to run external R code (create functions that run the code)
  - Enable the execution of Slices from R

1.5

- Depth priority to graph: and change Queue to PriorityQueue https://docs.python.org/3/library/queue.html

1.2

- Insert crumbs from existing functions without the decorator (read pydoc)
- Insert crumbs from existing objects without any decorator etc

1.1

- Default values in crumbs/functions

0.4

- Block editing attached Slice? By default on the WebUI it should not be possible to "see inside" (probably add a file link to open it in another tab or something)

0.3

- Slicer: status and outputs on each node execution
  - Present on WebUI
- WebUI: icons to crumbs (some pre-defined and others from path initialising crumb)

0.2

- WebUI: view file, list of crumbs, place crumbs as nodes, run graph get overall output

###### Tests

Test: `python -m pytest`

Coverage test: `python -m pytest --cov=src --cov-report xml:cov.xml tests/`
