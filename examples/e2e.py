import logging
import sys

formatter = logging.Formatter('%(asctime)s [%(levelname)-9s][%(name)-20s] %(message)s')
sh= logging.StreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
helper_logger= logging.root
helper_logger.addHandler(sh)
helper_logger.setLevel(logging.INFO)
logger= helper_logger.getChild(__name__)

import pathlib
import tempfile

import argparse
import io
import asyncio
import json
from comfyui_utils import comfy
from comfyui_utils import gen_prompts
from PIL.Image import Image

async def run_base_and_refiner(address: str, user_string: str, output_path: pathlib.Path=None, sample_dir: pathlib.Path=None):
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
        logger.warning(warning)
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
        def __init__(self):
            self.sample_count=0
            self.sample_prefix= None
            if sample_dir is not None:
                sample_file_name= None
                while sample_file_name is None or pathlib.Path(sample_file_name).exists():
                    sample_file_name= pathlib.Path(tempfile.mktemp('.png', 'prompt_sample_', sample_dir))
                self.sample_prefix= sample_file_name.stem
        async def queue_position(self, position):
            logger.info(f"Queue position: #{position}")
        async def in_progress(self, node_id, progress, total):
            progress = f"{progress}/{total}" if total else None
            if node_id == 10:
                logger.info(f"Base: {progress}" if progress else "Base...")
            if node_id == 11:
                logger.info(f"Refiner: {progress}" if progress else "Refiner...")
            elif node_id == 17:
                logger.info("Decoding...")
            elif node_id == 19:
                logger.info("Saving image on backend...")
        async def completed(self, outputs, cached):
            result["output"] = outputs
            result["cached"] = cached
        async def image_received(self, image: Image):
            if sample_dir is not None:
                sample_file= None
                while sample_file is None or sample_file.exists():
                    sample_file= sample_dir.joinpath(f"{self.sample_prefix}_{self.sample_count:04d}.png")
                    self.sample_count+= 1
                logger.info("Save sample file : %s", sample_file.name)
                image.save(sample_file)

    # Run the prompt and print the result.
    logger.info("Queuing workflow.")
    try:
        await comfyui.submit(prompt, Callbacks())
    except ValueError as e:
        logger.error("Error processing template: %s", e)
        return
    logger.info(f"Result (cached: {'yes' if result['cached'] else 'no'}): {result['output']}")

    # Write the result to a local file.
    if output_path is not None:
        backend_filepath = result["output"]["images"][0]
        async def on_load(data_file : io.BytesIO):
            with open(output_path, "wb") as f:
                f.write(data_file.getbuffer())
        logger.info("Saving backend image %s to %s", backend_filepath.get("filename", None), output_path)
        await comfyui.fetch(backend_filepath, on_load)


def main():
    parser = argparse.ArgumentParser(description='Run an SDXL or other workflow on a deployed ComfyUI server.')
    parser.add_argument("--address", type=str, help="the ComfyUI endpoint", required=True)
    parser.add_argument("--prompt", type=str, help="the user prompt", required=True)
    parser.add_argument("--output_path", type=pathlib.Path, help="The filename to store the final image received from ComfyUI", default=None)
    parser.add_argument("--output_dir", type=pathlib.Path, help="A folder to store the final image received from ComfyUI, name will be prompt_RANDOM.png", default=None)
    parser.add_argument("--sample_dir", type=pathlib.Path, help="Folder to store sample images received from ComfyUI, images names will be prompt_sample_RANDOM_COUNTER.png", default=None)
    args = parser.parse_args()

    outfile=args.output_path
    if outfile is None and args.output_dir is not None:
        if not args.output_dir.is_dir():
            logger.error("Argument --output_dir is %s but it's not a directory (full path resolved: %s)", args.output_dir, args.output_dir.resolve())
            exit(1)
        #Find a temporary name for the samples
        while outfile is None or pathlib.Path(outfile).exists():
            outfile= pathlib.Path(tempfile.mktemp('.png', 'prompt_', args.output_dir))
        logger.debug("(%s) %r", type(outfile), outfile)
    if args.sample_dir is not None and not args.sample_dir.is_dir():
            logger.error("Argument --sample_dir is %s but it's not a directory (full path resolved: %s)", args.sample_dir, args.sample_dir.resolve())
            exit(1)
        
    asyncio.run(run_base_and_refiner(args.address, args.prompt, outfile, args.sample_dir))

if __name__ == "__main__":
    main()