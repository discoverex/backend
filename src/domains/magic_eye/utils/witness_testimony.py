import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.configs.setting import BASE_DIR, OPENAI_API_KEY
from src.utils.logger import error, warning


class WitnessTestimonyGenerator:
    """매직아이 이미지 설명을 바탕으로 목격자 증언을 생성하는 유틸리티"""

    def __init__(self):
        # OpenAI API 키가 없는 경우를 대비한 방어 로직
        if not OPENAI_API_KEY:
            warning("OPENAI_API_KEY가 설정되지 않았습니다. 목격자 증언 생성 기능이 제한될 수 있습니다.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

        # 프롬프트 파일 경로 설정
        self.prompt_path = BASE_DIR / "src" / "domains" / "magic_eye" / "prompts" / "witness_testimony.md"
        system_prompt = self._load_prompt()

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "이미지 묘사 정보: {description}")
        ])
        self.chain = (self.prompt_template | self.llm | StrOutputParser()) if self.llm else None

    def _load_prompt(self) -> str:
        """외부 md 파일에서 시스템 프롬프트를 읽어옴"""
        try:
            if self.prompt_path.exists():
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            
            warning(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}. 기본 프롬프트를 사용합니다.")
        except Exception as e:
            error(f"프롬프트 파일 로드 중 오류 발생: {str(e)}")
        
        # 파일이 없거나 오류 발생 시 사용할 기본 프롬프트
        return "당신은 신비로운 현상을 목격한 증인입니다. 당신이 본 형체에 대해 구체적인 이름 없이 묘사해 주세요."

    def clean_description(self, description: str, asset_id: str) -> str:
        """불필요한 상용구 및 대상 이름을 제거하여 묘사 정보만 남김"""
        # 1. 공통 상용구 제거 (대소문자 무시)
        clean_text = re.sub(r"a 3d smooth white clay model of", "", description, flags=re.IGNORECASE)
        
        # 2. 대상 이름(asset_id) 제거
        if asset_id:
            # 단어 경계를 포함하여 제거
            clean_text = re.sub(rf"\b{asset_id}\b", "something", clean_text, flags=re.IGNORECASE)
            # asset_id가 언더바(_)를 포함할 수 있으므로 공백으로 치환된 경우도 고려
            clean_text = re.sub(rf"\b{asset_id.replace('_', ' ')}\b", "something", clean_text, flags=re.IGNORECASE)

        return clean_text.strip()

    async def generate_testimony(self, description: str, asset_id: str) -> str:
        """LLM을 사용하여 목격자 증언 생성"""
        if not self.chain:
            return "그것에 대해 말하기가 너무 두렵군요... 정체를 알 수 없는 무언가였습니다."

        try:
            # 1. 전처리
            cleaned_info = self.clean_description(description, asset_id)
            
            # 2. LLM 호출
            testimony = await self.chain.ainvoke({"description": cleaned_info})
            return testimony.strip()
        except Exception as e:
            error(f"목격자 증언 생성 중 오류 발생: {str(e)}")
            return "너무 순식간이라 제대로 묘사하기가 어렵네요. 신비로운 기운만 느껴졌습니다."
