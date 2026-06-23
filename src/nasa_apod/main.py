"""
date 	YYYY-MM-DD 	today 	The date of the APOD image to retrieve
start_date 	YYYY-MM-DD 	none 	The start of a date range, when requesting date for a range of dates. Cannot be used with date.
end_date 	YYYY-MM-DD 	today 	The end of the date range, when used with start_date.
count 	int 	none 	If this is specified then count randomly chosen images will be returned. Cannot be used with date or start_date and end_date.
thumbs 	bool 	False 	Return the URL of video thumbnail. If an APOD is not a video, this parameter is ignored.
api_key 	string 	DEMO_KEY 	api.nasa.gov key for expanded usage

sample output:
    {'date': '2026-06-23', 'explanation': "What would it look like to fly past Triton, the largest moon of planet Neptune?  Only one spacecraft has ever done this -- and the images of this dramatic encounter have been gathered into a video.  In 1989, the Voyager 2 robotic spacecraft shot through the Neptune system with cameras blazing.  Triton is slightly smaller than Earth's Moon but has ice volcanoes and a surface rich in frozen nitrogen.  The first sequence in the video shows Voyager's approach to Triton, which, with the exception of an overall false green tint, appears in approximately true color.  The mysterious cantaloupe terrain seen under the spacecraft soon changed from light to dark, with the terminator of night crossing underneath.  After closest approach, Voyager pivoted to see the departing moon, now visible as a diminishing crescent.  In 2015, the robotic New Horizons spacecraft famously flew past Pluto, an orb of similar size to Triton.   Almost Hyperspace: Random APOD Generator", 'media_type': 'video', 'service_version': 'v1', 'title': "Flying Past Neptune's Moon Triton", 'url': 'https://apod.nasa.gov/apod/image/2606/TritonPass_voyager2.mp4'}
"""

from datetime import datetime, timedelta
from enum import StrEnum

import httpx
import typer
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console


class Settings(BaseSettings):
    nasa_api_key: str
    model_config = SettingsConfigDict(env_file=".env")


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class ServiceVersion(StrEnum):
    V1 = "v1"
    V2 = "v2"


class APODResult(BaseModel):
    date: str = Field(max_length=10)
    explanation: str
    media_type: MediaType
    service_version: ServiceVersion
    title: str
    url: HttpUrl


setting = Settings()

APOD_API_URL = "https://api.nasa.gov/planetary/apod"

tool = typer.Typer()


@tool.command()
def get_images(days: int = 5):
    start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
    console = Console()
    with httpx.Client(timeout=30) as client:
        try:
            response = client.get(
                APOD_API_URL,
                params={"api_key": setting.nasa_api_key, "start_date": start_date},
            )
        except httpx.ReadTimeout:
            console.print("Timeout", style="bold red")
            return
        except httpx.HTTPStatusError as e:
            console.print(f"HTTP error: {e.response.status_code}", style="bold red")
            return
        response.raise_for_status()
        display_results([APODResult(**result) for result in response.json()])


def display_results(results: list[APODResult]):
    console = Console(force_terminal=True)
    for result in results:
        if result.media_type == MediaType.IMAGE:
            console.print(f"[link={result.url}]{result.title}[/link]", highlight=False)


def run():
    tool()


if __name__ == "__main__":
    run()
