import io
import os
import random
import shutil
from datetime import datetime

import torch
from diffusers import StableDiffusionPipeline
from transformers import pipeline

from src.configs.setting import APP_ENV
from src.domains.magic_eye.consts.generated_image import GeneratedImage, TargetDetails
from src.domains.magic_eye.consts.magic_eye_assets import MAGIC_EYE_ASSETS
from src.domains.magic_eye.utils.stereogram import create_stereogram


class MagicEyeService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # 1. Stable Diffusion 모델 로드 (이미지 생성용)
        self.sd_pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # 2. Depth Estimation 모델 로드 (깊이 맵 추출용)
        self.depth_estimator = pipeline(
            "depth-estimation",
            model="Intel/dpt-large",
            device=0 if self.device == "cuda" else -1
        )

        self.assets = MAGIC_EYE_ASSETS

    def _clear_debug_folder(self, folder_path: str):
        """디버그 폴더 내의 모든 파일 삭제"""
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.is_link(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")

    async def generate_random_game(self) -> GeneratedImage:
        """저장된 에셋 풀에서 랜덤하게 사물을 골라 매직아이 세트를 생성합니다."""

        # 1. 랜덤 사물 선택
        target = random.choice(self.assets)
        print(f"🎯 Selected Target: {target['display_name']} ({target['id']})")

        # 2. 프롬프트 구성 (그림자 억제를 위한 Negative Prompt 강화)
        refined_prompt = f"{target['prompt']}, flat lighting, no shadows, white background, high contrast"
        negative_prompt = "shadows, shading, highlights, gradient, realistic texture, blurry, background details, soft edges"

        # 3. 이미지 생성 (Stable Diffusion)
        raw_image = self.sd_pipe(
            prompt=refined_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=25
        ).images[0]

        # 4. Depth Map 추출 및 가공
        depth_result = self.depth_estimator(raw_image)
        depth_map = depth_result["depth"]  # 이것이 '정답' 이미지

        # 5. 매직아이(Stereogram) 합성
        magic_eye_img = create_stereogram(depth_map)

        # 6. 결과물을 바이너리(Bytes)로 변환
        # 문제 이미지 (Stereogram)
        prob_io = io.BytesIO()
        magic_eye_img.save(prob_io, format='PNG')
        prob_bytes = prob_io.getvalue()

        # 정답 이미지 (Depth Map)
        ans_io = io.BytesIO()
        depth_map.save(ans_io, format='PNG')
        ans_bytes = ans_io.getvalue()

        # 로컬 개발 환경이라면 문제/정답 이미지 저장 → 디버그 용
        if APP_ENV == "local":
            debug_path = "debug_outputs"
            # 기존 파일들 전부 제거
            self._clear_debug_folder(debug_path)
            # 폴더 재생성
            os.makedirs(debug_path, exist_ok=True)
            # 새 이미지 저장
            timestamp = datetime.now().strftime("%H%M%S")
            magic_eye_img.save(f"{debug_path}/{timestamp}_{target['id']}_problem.png")
            depth_map.save(f"{debug_path}/{timestamp}_{target['id']}_answer.png")

        # 7. 전체 데이터 패키징 반환
        return GeneratedImage(
            problem_image=prob_bytes,
            answer_image=ans_bytes,
            target_info=TargetDetails(
                id=target['id'],
                display_name=target['display_name'],
                keywords=target['keywords'],
            )
        )