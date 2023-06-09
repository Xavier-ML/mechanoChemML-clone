#!/usr/bin/env python
import os
from mechanoChemML.workflows.active_learning.active_learning import Active_learning

input_path = os.path.dirname(__file__)
if input_path: # when it is not ''
    input_path += '/NiAl_free_energy.ini'
else:
    input_path = 'NiAl_free_energy.ini' 

workflow = Active_learning(input_path)
workflow.main_workflow()