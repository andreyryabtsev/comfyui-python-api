"""End-to-end example for creating an image with SDXL base + refiner"""

import argparse
import io
import asyncio
import json
from comfyui_utils import comfy
from comfyui_utils import gen_prompts

async def run_base_and_refiner(address: str, user_string: str, output_path=None):
    comfyui = comfy.ComfyAPI(address)

    # Load the stored API format prompt.
    with open("examples/workflows/sdxl.json", "r", encoding="utf-8") as f:
        PROMPT_TEMPLATE = f.read()
    prompt = json.loads(PROMPT_TEMPLATE)
    # Config for parsing user arguments:
    prompt_config = gen_prompts.make_config("GenImg", [
        gen_prompts.IntArg("base_steps", default_value=14, min_value=1, max_value=80),
        gen_prompts.IntArg("refiner_steps", default_value=5, min_value=0, max_value=40),
        gen_prompts.IntArg("seed", default_value=0, min_value=0, max_value=1e10)
    ])
    # Extract the arguments from the user string.
    # Throws ValueError if arguments are unrecognized or malformed.
    # Returns a list of warnings if any argument is invalid.
    parsed = gen_prompts.parse_args(user_string, prompt_config)
    for warning in parsed.warnings:
        print(f"WARNING: {warning}")
    # Adjust the prompt with user args.
    prompt["6"]["inputs"]["text"] = parsed.cleaned
    prompt["10"]["inputs"]["end_at_step"] = parsed.result.base_steps
    prompt["11"]["inputs"]["start_at_step"] = parsed.result.base_steps
    prompt["10"]["inputs"]["steps"] = parsed.result.base_steps + parsed.result.refiner_steps
    prompt["10"]["inputs"]["noise_seed"] = parsed.result.seed
    prompt["11"]["inputs"]["steps"] = parsed.result.base_steps + parsed.result.refiner_steps

    # Prepare result dictionary.
    result = {
        "output": {},
        "cached": False
    }
    # Configure the callbacks which will write to it during execution while printing updates.
    class Callbacks(comfy.Callbacks):
        async def queue_position(self, position):
            print(f"Queue position: #{position}")
        async def in_progress(self, node_id, progress, total):
            progress = f"{progress}/{total}" if total else None
            if node_id == 10:
                print(f"Base: {progress}" if progress else "Base...")
            if node_id == 11:
                print(f"Refiner: {progress}" if progress else "Refiner...")
            elif node_id == 17:
                print("Decoding...")
            elif node_id == 19:
                print("Saving image on backend...")
        async def completed(self, outputs, cached):
            result["output"] = outputs
            result["cached"] = cached

    # Run the prompt and print the result.
    print("Queuing workflow.")
    await comfyui.submit(prompt, Callbacks())
    print(f"Result (cached: {'yes' if result['cached'] else 'no'}):\n{result['output']}")

    # Write the result to a local file.
    if output_path is not None:
        backend_filepath = result["output"]["images"][0]
        async def on_load(data_file : io.BytesIO):
            with open(output_path, "wb") as f:
                f.write(data_file.getbuffer())
        await comfyui.fetch(backend_filepath, on_load)


def main():
    parser = argparse.ArgumentParser(description='Run an SDXL or other workflow on a deployed ComfyUI server.')
    parser.add_argument("--address", type=str, help="the ComfyUI endpoint", required=True)
    parser.add_argument("--prompt", type=str, help="the user prompt", required=True)
    parser.add_argument("--output_path", type=str, help="the output path", default=None)
    args = parser.parse_args()

    asyncio.run(run_base_and_refiner(args.address, args.prompt, args.output_path))

if __name__ == "__main__":
    main()
