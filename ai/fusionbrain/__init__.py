import asyncio
import aiohttp
import json
import base64
import io
import requests
from . import exceptions

class AIArtist:
    def __init__(self, url: str, api_key: str, secret_key: str):
        self.URL = url
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}",
        }

    async def generate(
        self,
        prompt: str,
        style: str,
        negative_prompt: str | None = None,
        images_num: int = 1,
        width: int = 1024,
        height: int = 1024,
    ):
        async with aiohttp.ClientSession() as session:
            model_id = await self.__get_kandinsky_id(session)
            # availability = await self.__get_availability(session, model_id)
            data = self.__get_data(
                model_id, prompt, negative_prompt, style, images_num, width, height
            )
            uuid = await self.__get_request_uuid(session, data)
            if uuid == "DISABLED_BY_QUEUE":
                raise exceptions.APIDisabled()
            base64_img, is_censored = await self.__check_generation(session, uuid)
            
            return io.BytesIO(base64.b64decode(base64_img)), is_censored

    # async def __get_availability(self, session: aiohttp.ClientSession, model_id: int):
    #     params = {'model_id': '1'}
    #     async with session.get(self.URL + f'key/api/v1/text2image/availability', headers=self.AUTH_HEADERS, params=params) as res:
    #         return res['model_status']

    async def __get_kandinsky_id(self, session: aiohttp.ClientSession):
        async with session.get(
            self.URL + "key/api/v1/models", headers=self.AUTH_HEADERS
        ) as res:
            data = await res.json()
        return data[0]["id"]

    async def __get_request_uuid(self, session: aiohttp.ClientSession, request_data: dict):
        # headers = self.AUTH_HEADERS.copy()
        # headers['Content-Type'] = 'application/json'
        # async with session.post(
        #     self.URL + "key/api/v1/text2image/run",
        #     headers=headers,
        #     json=request_data,
        # ) as res:
        #     res_json = await res.json()
        res = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=request_data)
        res_json = res.json()
        return res_json["uuid"]

    async def __check_generation(
        self,
        session: aiohttp.ClientSession,
        uuid: str,
        attempts: int = 10,
        delay: int = 5,
    ):
        while attempts > 0:
            async with session.get(
                self.URL + "key/api/v1/text2image/status/" + uuid,
                headers=self.AUTH_HEADERS,
            ) as res:
                data = await res.json()
            if data["status"] == "DONE":
                return data["images"][0], data['censored']
            elif data["status"] == "FAIL":
                raise exceptions.FailedGeneration(data["errorDescription"])

            attempts -= 1
            await asyncio.sleep(delay)

    def __get_params(
        self,
        prompt: str,
        negative_prompt: str | None,
        style: str,
        images_num: int,
        width: int,
        height: int,
    ):
        params = {
            "type": "GENERATE",
            "numImages": images_num,
            "width": width,
            "height": height,
            "style": style,
            "generateParams": {"query": f"{prompt}"},
        }
        if negative_prompt:
            params.setdefault("negativePromptUnclip", negative_prompt)
        return params

    def __get_data(
        self,
        model_id: int,
        prompt: str,
        negative_prompt: str | None,
        style: str,
        images_num: int,
        width: int,
        height: int,
    ):
        params = self.__get_params(
            prompt, negative_prompt, style, images_num, width, height
        )
        return {
            "model_id": (None, str(model_id)),
            "params": (None, json.dumps(params, indent=4), "application/json"),
        }
        