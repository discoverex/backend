import json
import random

from fastapi import HTTPException, status

from src.configs.setting import BASE_DIR, IMAGE_BUCKET_NAME
from src.domains.magic_eye.dtos.magic_eye_dtos import (
    MagicEyeCandidate,
    MagicEyeCorrectAnswer,
    MagicEyeMetadataQuery,
    MagicEyeQuizResponse,
)
from src.domains.magic_eye.utils.gcs_image_loader import (
    GCSImageLoader,
    get_gcs_image_loader,
)
from src.domains.magic_eye.utils.gcs_model_loader import get_gcs_model_loader
from src.domains.magic_eye.utils.witness_testimony import WitnessTestimonyGenerator
from src.utils.logger import logger


class MagicEyeService:
    def __init__(self):
        """매직아이 서비스의 기본 골격입니다."""
        self.image_loader = get_gcs_image_loader()
        self.model_loader = get_gcs_model_loader()
        self.witness_generator = WitnessTestimonyGenerator()
        self.metadata_path = BASE_DIR / "src" / "domains" / "magic_eye" / "consts" / "magic_eye_metadata.json"
        self.bucket_name = IMAGE_BUCKET_NAME

    def _get_unique_metadata(self, metadata: list[dict]) -> list[dict]:
        """problem_path를 기준으로 중복된 메타데이터를 제거합니다."""
        seen_paths = set()
        unique_metadata = []
        for item in metadata:
            p_path = item.get("problem_path")
            if p_path and p_path not in seen_paths:
                unique_metadata.append(item)
                seen_paths.add(p_path)
        return unique_metadata

    async def get_magic_eye_quiz(self, count: int = 5) -> tuple[MagicEyeQuizResponse, str | None]:
        """
        객관식 매직아이 퀴즈를 출제합니다.
        로컬 메타데이터에서 요청한 개수(count)만큼 랜덤 추출하고 서명된 URL을 생성합니다.
        LLM을 활용하여 목격자 증언을 생성합니다.
        """
        try:
            message = None
            if count < 5:
                count = 5
                message = "퀴즈 후보 개수가 최소값(5)보다 작아 5개로 조정되었습니다."
            elif count > 50:
                count = 50
                message = "퀴즈 후보 개수가 최대값(50)보다 커 50개로 조정되었습니다."

            if not self.metadata_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="매직아이 메타데이터 파일이 존재하지 않습니다. 서버가 정상적으로 시작되었는지 확인하세요."
                )

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                all_metadata = json.load(f)

            # 중복 데이터 제거 (파일 경로 기준)
            all_metadata = self._get_unique_metadata(all_metadata)

            if len(all_metadata) < count:
                # 부족할 경우 에러 대신 현재 가능한 최대치로 조정
                message = f"요청하신 개수({count}개)보다 사용 가능한 유니크 이미지 개수({len(all_metadata)}개)가 적어 전체 이미지를 반환합니다."
                count = len(all_metadata)
                
                if count < 1:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="사용 가능한 매직아이 메타데이터가 없습니다."
                    )

            # 요청한 개수만큼 랜덤 샘플링
            samples = random.sample(all_metadata, count)
            candidates = []

            for i, item in enumerate(samples):
                p_path = item.get("problem_path", "").replace("\\", "/")
                a_path = item.get("answer_path", "").replace("\\", "/")

                if p_path and not p_path.startswith("magic-eye/"):
                    p_path = f"magic-eye/{p_path}"
                if a_path and not a_path.startswith("magic-eye/"):
                    a_path = f"magic-eye/{a_path}"

                p_url = self.image_loader.generate_signed_url(p_path, bucket_name=self.bucket_name)
                a_url = self.image_loader.generate_signed_url(a_path, bucket_name=self.bucket_name)

                candidates.append(MagicEyeCandidate(
                    id=i,
                    asset_id=item.get("asset_id"),
                    display_name=item.get("display_name"),
                    problem_url=p_url or "",
                    answer_url=a_url or ""
                ))

            # 정답 하나 선택
            correct_idx = random.randint(0, count - 1)
            correct_item = candidates[correct_idx]
            
            # 3. 오직 정답에 대해서만 목격자 증언 생성 (토큰 최적화)
            # 메타데이터에서 해당 정답의 원본 설명을 찾음
            correct_metadata = samples[correct_idx]
            testimony = await self.witness_generator.generate_testimony(
                description=correct_metadata.get("description", ""),
                asset_id=correct_metadata.get("asset_id", "")
            )

            return MagicEyeQuizResponse(
                total_count=len(candidates),
                candidates=candidates,
                correct_answer=MagicEyeCorrectAnswer(
                    id=correct_idx,
                    asset_id=correct_item.asset_id,
                    description=testimony
                )
            ), message

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"매직아이 퀴즈 생성 중 오류 발생: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"퀴즈 생성 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_magic_eye_metadata(self, query: MagicEyeMetadataQuery = None) -> list[dict]:
        """
        로컬 JSON 파일에서 매직아이 메타데이터를 읽어오고 필터링하여 반환합니다.
        """
        try:
            if not self.metadata_path.exists():
                logger.error(f"메타데이터 파일이 존재하지 않습니다: {self.metadata_path}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="매직아이 메타데이터 파일을 찾을 수 없습니다. 서버가 정상적으로 시작되었는지 확인하세요."
                )

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # 중복 데이터 제거 (이미지 경로 기준)
            metadata = self._get_unique_metadata(metadata)

            # 필터링 적용
            if query:
                if query.asset_id:
                    metadata = [row for row in metadata if row.get("asset_id") == query.asset_id]
                if query.file_number is not None:
                    metadata = [row for row in metadata if row.get("file_number") == query.file_number]

            return metadata

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"매직아이 메타데이터 조회 중 오류 발생: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"메타데이터 조회 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_model_download_url(self, model_filename: str) -> str | None:
        """
        프론트엔드 WebGPU 가속을 위해 비공개 버킷의 모델 접근용 서명된 URL을 생성합니다.
        파일 존재 여부를 먼저 확인한 후, 존재할 경우에만 15분 유효한 URL을 반환합니다.
        """
        try:
            # 경로 조합 (models/onnx/파일명.onnx)
            blob_path = f"models/onnx/{model_filename}"

            # 1. 파일 존재 여부 확인
            if not self.model_loader.check_model_exists(blob_path):
                logger.warning(f"모델 파일을 찾을 수 없습니다: {blob_path}")
                return None

            # 2. 존재할 경우 15분(15) 유효한 URL 생성
            signed_url = self.model_loader.generate_signed_url(
                blob_name=blob_path,
                expiration_minutes=15
            )

            # 결과 반환 (3항 연산자 사용)
            return signed_url if signed_url else None

        except Exception as e:
            logger.error(f"모델 서명 URL 생성 중 오류 발생: {str(e)}")
            return None
