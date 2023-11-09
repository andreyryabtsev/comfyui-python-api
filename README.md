# ComfyUI utils

This package provides simple utils for:
1. Parsing out prompt arguments, e.g. "a beautiful forest $num_steps=12"
2. Running a workflow in parsed API format against a ComfyUI endpoint, with callbacks for specified events.

It's designed primarily for developing casual chatbots (e.g. a Discord bot) where users can adjust certain parameters and receive live progress updates.

Limitations:
- Only integer arguments are currently supported in addition to the prompt itself. The plan is to add at least floats and strings.
- Only one output from the workflow is supported.

## Example.

To test the library with a sample SDXL workflow, clone this repository and run (replacing the address):

```
pip install -e .
python examples/e2e.py\
  --address='192.168.0.10:11010'\
  --prompt='a smiling potato $base_steps=8$refiner_steps=3'\
  --output='./potato.png'
```
The single quotes are important so your shell doesn't try to parse the `$`'s. Expected output:
```
Queuing workflow.
Queue position: #0
Base...
Base: 1/8
Base: 2/8
Base: 3/8
Base: 4/8
Base: 5/8
Base: 6/8
Base: 7/8
Base: 8/8
Refiner...
Refiner: 1/3
Refiner: 2/3
Refiner: 3/3
Decoding...
Saving image on backend...
Result (cached: no):
{'images': [{'filename': 'ComfyUI_00101_.png', 'subfolder': '', 'type': 'output'}]}
```
The file will be saved in the root directory.

## Use your own workflow.

After finalizing the workflow, use the "Save (API format)" button to store the workflow. Then, edit the `PromptConfig` in the script to reflect the arguments you wish to make available, and ensure the prompt has them replaced after parsing.
