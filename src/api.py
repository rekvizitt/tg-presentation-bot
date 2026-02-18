import asyncio
import configparser
import json
import re

from openai import AsyncOpenAI

config = configparser.ConfigParser()
config.read("settings.ini")
api_key = config.get("API", "api_key")


class PresentationAPI:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

    def _clean_text(self, text: str) -> str:
        """Удаляет символы Markdown (жирность, курсив и т.д.)"""
        return re.sub(r"[\*\-_#`]", "", text).strip()

    def _extract_json(self, text: str) -> str:
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        return match.group(0) if match else text

    async def generate_topics(self, theme: str, slides_count: int) -> dict[int, str]:
        prompt = (
            f"Generate short topics for {slides_count} slides about '{theme}'. "
            'Output ONLY raw JSON format: {"1": "Topic", ...}'
        )
        completion = await self.client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Output ONLY JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(self._extract_json(completion.choices[0].message.content))
            return {int(k): self._clean_text(v) for k, v in data.items()}
        except:
            return {i: f"Topic {i}" for i in range(1, slides_count + 1)}

    async def generate_slide_content(self, theme: str, slide_topic: str) -> list[str]:
        """Генерирует список тезисов без разметки Markdown."""
        prompt = (
            f"Provide 3-5 bullet points for a slide about '{slide_topic}' "
            f"in a presentation about '{theme}'. Language: Russian. "
            "Return ONLY a JSON object with a key 'points' containing a list of strings. "
            'Do not use markdown bold or italic. Example: {"points": ["Point 1", "Point 2"]}'
        )

        completion = await self.client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional copywriter. Output ONLY JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        try:
            raw_json = self._extract_json(completion.choices[0].message.content)
            data = json.loads(raw_json)
            points = data.get("points", [])
            # Очищаем каждую строку от случайных символов разметки
            return [self._clean_text(p) for p in points]
        except:
            return ["Не удалось загрузить содержимое"]
