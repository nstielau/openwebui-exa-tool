"""
title: Exa Web Search Tool
author: Nick Stielau
author_url: https://github.com/nstielau
git_url: https://github.com/nstielau/openwebui-exa-tool.git
description: This tool integrates Exa for web searching within OpenWebUI.
required_open_webui_version: 0.4.0
requirements: exa_py, fire, python-dotenv
version: 0.2.0
licence: MIT
"""

import asyncio
import json
import fire
import os
from typing import Any, Callable
from dotenv import load_dotenv

from exa_py import Exa
from pydantic import BaseModel, Field


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )

load_dotenv()

class Tools:
    class Valves(BaseModel):
        EXA_API_KEY: str = Field(
            default=os.getenv("EXA_API_KEY", "EXA_API_KEY"),
            description="API key for Exa",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def search_web(
        self,
        query: str,
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Search the web using Exa and get the content of the relevant pages.
        :param query: Web Query used in search engine.
        :return: The content of the pages in json format.
        """
        exa = Exa(api_key=self.valves.EXA_API_KEY)
        emitter = EventEmitter(__event_emitter__)

        await emitter.emit(f"Initiating Exa web search for: {query}")

        try:
            await emitter.emit("Performing Exa search")
            search_results = exa.search_and_contents(query=query, type='auto', highlights=True)
            await emitter.emit(f"Retrieved Exa search results")

        except Exception as e:  # Consider using a more specific exception
            await emitter.emit(
                status="error",
                description=f"Error during Exa search: {str(e)}",
                done=True,
            )
            raise e
            return json.dumps({"error": str(e)})

        await emitter.emit(
            status="complete",
            description=f"Exa web search completed. Retrieved content from search results.",
            done=True,
        )
        return str(search_results)


def cli(query: str):
    tools = Tools()
    async def stdout_emitter(event):
        print(json.dumps(event))

    result = asyncio.run(tools.search_web(query, __event_emitter__=stdout_emitter))
    print(result)

if __name__ == "__main__":
    import sys
    import unittest
    from unittest.mock import AsyncMock, patch

    class TestExaForOpenWebUI(unittest.TestCase):
        def setUp(self):
            self.tools = Tools()
            self.tools.valves.EXA_API_KEY = "test_api_key"

        @patch('exa_py.Exa.search_and_contents', new_callable=AsyncMock)
        async def test_search_web_success(self, mock_search_and_contents):
            mock_search_and_contents.return_value = {"results": "some content"}
            result = await self.tools.search_web("test query")
            self.assertIn("some content", result)

        @patch('exa_py.Exa.search_and_contents', new_callable=AsyncMock)
        async def test_search_web_failure(self, mock_search_and_contents):
            mock_search_and_contents.side_effect = Exception("Test error")
            result = await self.tools.search_web("test query")
            self.assertIn("error", result)

    if len(sys.argv) > 1 and sys.argv[1] == "tests":
        unittest.main(argv=sys.argv[:1])
    else:
        fire.Fire(cli)
