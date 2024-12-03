"""
title: Exa Web Search Tool
author: Nick Stielau
author_url: https://github.com/nstielau
git_url: https://github.com/nstielau/openwebui-exa-tool.git
description: This tool integrates Exa for web searching within OpenWebUI.
required_open_webui_version: 0.4.0
requirements: exa_py
version: 0.1.0
licence: MIT
"""

import asyncio
import json
from typing import Any, Callable

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

class Tools:
    class Valves(BaseModel):
        EXA_API_KEY: str = Field(
            default="EXA_API_KEY",
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
            return json.dumps({"error": str(e)})

        await emitter.emit(
            status="complete",
            description=f"Exa web search completed. Retrieved content from search results.",
            done=True,
        )
        return str(search_results)
