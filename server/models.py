from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
MODEL = 'qwen3-tts-instruct-flash-2026-01-26'
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    @model_validator(mode='before')
    @classmethod
    def valid_storage_text(cls, value):
        # PostgreSQL text/jsonb disallow NUL; reject invalid Unicode before SQL,
        # password hashing or JSON responses can turn bad input into a 500.
        def check(item):
            if isinstance(item, str):
                if '\x00' in item:
                    raise ValueError('文本不能包含空字符')
                try:
                    item.encode('utf-8')
                except UnicodeEncodeError:
                    raise ValueError('文本包含无效 Unicode 字符') from None
            elif isinstance(item, dict):
                for key, nested in item.items():
                    check(key)
                    check(nested)
            elif isinstance(item, (list, tuple)):
                for nested in item:
                    check(nested)
        check(value)
        return value
class Mix(Strict):
    intro_seconds: float = Field(ge=0,le=30)
    tail_seconds: float = Field(ge=0,le=180)
    fade_out_seconds: float = Field(ge=0,le=180)
    ambience_dbfs: float = Field(ge=-60,le=-25)
    seed: int = Field(ge=0,lt=2**32)
    @model_validator(mode='after')
    def fades(self):
        if self.fade_out_seconds > self.tail_seconds: raise ValueError('渐弱时间不能超过尾声')
        return self
class Segment(Strict):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    label: str = Field(default='', max_length=80)
    text: str = Field(min_length=1,max_length=600)
    pause_after_seconds: float = Field(ge=0,le=60)
    @field_validator('text')
    @classmethod
    def clean_text(cls,v):
        if not v.strip() or re.search(r'[\[\]<>【】]',v): raise ValueError('正文不能为空或含制作标记')
        return v
class Script(Strict):
    version: Literal[1]
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    title: str = Field(min_length=1,max_length=100)
    model: Literal['qwen3-tts-instruct-flash','qwen3-tts-instruct-flash-2026-01-26']
    voice: Literal['Serena','Ethan']
    language_type: Literal['Chinese']
    instructions: str = Field(min_length=1,max_length=600)
    mix: Mix
    segments: list[Segment] = Field(min_length=1,max_length=20)
    @model_validator(mode='after')
    def limits(self):
        if len({s.id for s in self.segments}) != len(self.segments): raise ValueError('段落 id 必须唯一')
        if sum(len(s.text) for s in self.segments)>2400: raise ValueError('MVP 每份脚本最多 2400 字符')
        return self
class Preferences(Strict):
    voice: Literal['Serena','Ethan']='Serena'
    scene: Literal['rainy-inn']='rainy-inn'
    ambience_dbfs: float=Field(default=-38,ge=-60,le=-25)
    sleep_timer_minutes: Literal[0,15,30,45,60,-1]=30
class Register(Strict):
    email: str=Field(min_length=3,max_length=254)
    password: str=Field(min_length=10,max_length=128)
    display_name: str=Field(default='夜航旅人',min_length=1,max_length=50)
    invite_code: str=Field(default='',max_length=200)
class Login(Strict):
    email: str=Field(max_length=254)
    password: str=Field(max_length=128)
class Create(Strict):
    script: Script
    scene: Literal['rainy-inn']='rainy-inn'
class Patch(Strict):
    script: Script|None=None
    scene: Literal['rainy-inn']|None=None
class Generate(Strict):
    request_id: __import__('uuid').UUID
class Playback(Strict):
    position_seconds: float=Field(ge=0,le=86400)
    completed: bool=False
class TokenCreate(Strict):
    name: str=Field(min_length=1,max_length=60)
