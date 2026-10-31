# Waffle
Waffle is a feature modeling language enabling configuration of BRISE.

This module contains a front-end for the configuration process available at [localhost:8000](http://localhost:8000).

The workflow with this module is the following:
1. Launch BRISE as described in [the main Readme](../README.md#using-brise) 
2. Submit your feature model into the initialization window.
3. Walk through the configuration wizard steps. 
4. Put resulting `Json`-file into [main_node/Resources](../main_node/Resources) directory.

## Designing the SearchSpace visually

To minimize direct user interaction with the feature model, the
[`searchspace_editor`](../searchspace_editor/README.md) offers a complementary way to produce
the `SearchSpace` part of the `.wfl` model — a canvas-based editor for visually building it and exporting it as `.wfl` text, which must
then be manually merge into the full model (see `SearchSpace` placeholder) to be submitted in
step 2 of the workflow. It is reachable via the main BRISE dashboard's "Open Searchspace Editor" tab, or directly at
[localhost:3001](http://localhost:3001).
