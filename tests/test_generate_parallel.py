# Test to ensure the wrapper works with parallelism, do not spam the API !

from sys import path
from os import environ as env
from os.path import join, abspath, dirname

path.insert(0, abspath(join(dirname(__file__), '..')))

from novelai_api import NovelAIAPI
from novelai_api.Preset import Preset, Model
from novelai_api.GlobalSettings import GlobalSettings
from novelai_api.Tokenizer import Tokenizer
from novelai_api.utils import b64_to_tokens

from aiohttp import ClientSession
from logging import Logger, StreamHandler
from asyncio import run, gather

import pytest

models = [*Model]

if "NAI_USERNAME" not in env or "NAI_PASSWORD" not in env:
    raise RuntimeError("Please ensure that NAI_USERNAME and NAI_PASSWORD are set in your environment")

username = env["NAI_USERNAME"]
password = env["NAI_PASSWORD"]

logger = Logger("NovelAI")
logger.addHandler(StreamHandler())


async def generate_5(api: NovelAIAPI, model: Model):
    await api.high_level.login(username, password)

    preset = Preset.from_default(model)
    global_settings = GlobalSettings(ban_brackets = True, bias_dinkus_asterism = True)

    logger.info(f"Using model {model.value}\n")

    input_txt = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam at dolor dictum, interdum est sed, consequat arcu. Pellentesque in massa eget lorem fermentum placerat in pellentesque purus. Suspendisse potenti. Integer interdum, felis quis porttitor volutpat, est mi rutrum massa, venenatis viverra neque lectus semper metus. Pellentesque in neque arcu. Ut at arcu blandit purus aliquet finibus. Suspendisse laoreet risus a gravida semper. Aenean scelerisque et sem vitae feugiat. Quisque et interdum diam, eu vehicula felis. Ut tempus quam eros, et sollicitudin ligula auctor at. Integer at tempus dui, quis pharetra purus. Duis venenatis tincidunt tellus nec efficitur. Nam at malesuada ligula."
    prompt = Tokenizer.encode(model, input_txt)

    preset["max_length"] = 20
    gens = [api.high_level.generate(prompt, model, preset, global_settings) for _ in range(5)]
    results = await gather(*gens)
    for i, gen in enumerate(results):
        logger.info(f"Gen {i}:")
        logger.info("\t" + Tokenizer.decode(model, b64_to_tokens(gen["output"])))
        logger.info("")


@pytest.mark.parametrize("model", models)
async def test_run_5_generate_sync(model: Model):
    # sync handler
    api = NovelAIAPI()
    await generate_5(api, model)


@pytest.mark.parametrize("model", models)
async def test_run_5_generate_async(model: Model):
    # async handler
    try:
        async with ClientSession() as session:
            api = NovelAIAPI(session)
            await generate_5(api, model)
    except Exception as e:
        await session.close()
        raise e

if __name__ == "__main__":
    async def main():
        await test_run_5_generate_sync(Model.Sigurd)
        await test_run_5_generate_async(Model.Sigurd)

    run(main())
