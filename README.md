# ComfyUI utils

This package provides simple utils for:
1. Parsing out prompt arguments, e.g. "a beautiful forest $num_steps=12"
2. Running a workflow in parsed API format against a ComfyUI endpoint, with callbacks for specified events.

It's designed primarily for developing casual chatbots (e.g. a Discord bot) where users can adjust certain parameters and receive live progress updates.

Limitations:
- Only integer arguments are currently supported in addition to the prompt itself. The plan is to add at least floats and strings.
- Only one output from the workflow is supported.

Supports:
- Arbitrary number of integer args embedded in the main string prompt.
- Queuing with a callback when the queue position changes.
- Fetching cached results.
- Reporting intermediate progress of nodes like `KSampler`.


## Install

```
pip install comfyui_utils
```

## Usage

(better docs are coming, for now please look at the source code / sample script)

```
from comfyui_utils import gen_prompts, comfy
gen_prompts.make_config("GenVid", [gen_prompts.IntArg("num_steps", default_value=12, min_value=1, max_value=80)])
...
try:
    parsed = gen_prompts.parse_args(raw_prompt, prompt_config)
except ValueError as e:
    print(f"Invalid prompt {e.args[0]}")
prompt_data = ...
class Callbacks(comfy.Callbacks):
    ...
await comfyui.submit(prompt_data, Callbacks())
def on_load(data_buffer):
    ...
await comfyui.fetch(backend_filepath, on_load)
```

## Example

To test the library with a sample SDXL workflow, run the following after installing (replace the address with your ComfyUI endpoint). Make sure your ComfyUI has `sd_xl_base_1.0.safetensors` and `sd_xl_refiner_1.0.safetensors` installed (or replace the workflow).

```python
comfy_ui_example_e2e\
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

## Use your own workflow

After finalizing the workflow, use the "Save (API format)" button to store the workflow. Then, edit the `PromptConfig` in the script to reflect the arguments you wish to make available, and ensure the prompt has them replaced after parsing.
