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

Program options :

```usage: e2e.py [-h] --address ADDRESS --prompt PROMPT [--output_path OUTPUT_PATH] [--output_dir OUTPUT_DIR] [--preview_dir PREVIEW_DIR]

Run an SDXL or other workflow on a deployed ComfyUI server.

options:
  -h, --help            show this help message and exit
  --address ADDRESS     the ComfyUI endpoint
  --prompt PROMPT       the user prompt
  --output_path OUTPUT_PATH
                        The filename to store the final image received from ComfyUI
  --output_dir OUTPUT_DIR
                        A folder to store the final image received from ComfyUI, name will be prompt_RANDOM.png
  --preview_dir PREVIEW_DIR
                        Folder to store preview images received from ComfyUI, images names will be prompt_preview_RANDOM_COUNTER.png
```
Example:
```python
comfy_ui_example_e2e\
  --address='192.168.0.10:11010'\
  --prompt='a smiling potato $base_steps=8$refiner_steps=3'\
  --output_path='./potato.png'
```
The single quotes are important so your shell doesn't try to parse the `$`'s. Expected output:
```
2023-12-18 22:23:37,441 [INFO     ][__main__            ] Queuing workflow.
2023-12-18 22:23:37,533 [INFO     ][root                ] {'prompt_id': 'ae431d7f-e212-4b05-8bcd-ebc8d346554f', 'number': 0, 'node_errors': {}}
2023-12-18 22:23:37,609 [INFO     ][__main__            ] Queue position: #0
2023-12-18 22:23:44,484 [INFO     ][__main__            ] Base...
2023-12-18 22:23:46,335 [INFO     ][__main__            ] Base: 1/8
2023-12-18 22:23:46,351 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:46,988 [INFO     ][__main__            ] Base: 2/8
2023-12-18 22:23:47,002 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:47,663 [INFO     ][__main__            ] Base: 3/8
2023-12-18 22:23:47,678 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:48,314 [INFO     ][__main__            ] Base: 4/8
2023-12-18 22:23:48,330 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:48,964 [INFO     ][__main__            ] Base: 5/8
2023-12-18 22:23:48,984 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:49,614 [INFO     ][__main__            ] Base: 6/8
2023-12-18 22:23:49,712 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:50,271 [INFO     ][__main__            ] Base: 7/8
2023-12-18 22:23:50,294 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:50,920 [INFO     ][__main__            ] Base: 8/8
2023-12-18 22:23:50,947 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:50,948 [INFO     ][__main__            ] Refiner...
2023-12-18 22:23:55,148 [INFO     ][__main__            ] Refiner: 1/3
2023-12-18 22:23:55,291 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:55,826 [INFO     ][__main__            ] Refiner: 2/3
2023-12-18 22:23:55,855 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:56,511 [INFO     ][__main__            ] Refiner: 3/3
2023-12-18 22:23:56,541 [INFO     ][root                ] Received an JPEG (PREVIEW_IMAGE)
2023-12-18 22:23:56,542 [INFO     ][__main__            ] Decoding...
2023-12-18 22:23:57,466 [INFO     ][__main__            ] Saving image on backend...
2023-12-18 22:23:57,901 [INFO     ][__main__            ] Result (cached: no): {'images': [{'filename': 'ComfyUI_00022_.png', 'subfolder': '', 'type': 'output'}]}
2023-12-18 22:23:57,901 [INFO     ][__main__            ] Saving backend image ComfyUI_00022_.png to potato.png
```
The file will be saved in the root directory.

## Use your own workflow

After finalizing the workflow, use the "Save (API format)" button to store the workflow. Then, edit the `PromptConfig` in the script to reflect the arguments you wish to make available, and ensure the prompt has them replaced after parsing.
