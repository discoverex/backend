import json
import random

from fastapi import HTTPException, status

from src.configs.setting import BASE_DIR, BUCKET_NAME
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
from src.utils.logger import logger


class MagicEyeService:
    def __init__(self, gcs_loader: GCSImageLoader = None):
        """매직아이 서비스의 기본 골격입니다."""
        self.gcs_loader = gcs_loader or get_gcs_image_loader()
        self.metadata_path = BASE_DIR / "src" / "domains" / "magic_eye" / "consts" / "magic_eye_metadata.json"
        self.bucket_name = BUCKET_NAME

    async def get_magic_eye_quiz(self, count: int = 5) -> tuple[MagicEyeQuizResponse, str | None]:
        """
        객관식 매직아이 퀴즈를 출제합니다.
        로컬 메타데이터에서 요청한 개수(count)만큼 랜덤 추출하고 서명된 URL을 생성합니다.
        count가 5 미만이면 5로, 50 초과면 50으로 자동 조정됩니다.
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

            if len(all_metadata) < count:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"메타데이터 건수가 퀴즈 출제에 부족합니다 (최소 {count}건 필요)."
                )

            # 요청한 개수만큼 랜덤 샘플링
            samples = random.sample(all_metadata, count)
            candidates = []

            for i, item in enumerate(samples):
                # GCS 서명된 URL 생성
                # 백슬래시를 슬래시로 통일 (윈도우 경로 대응)
                p_path = item.get("problem_path", "").replace("\\", "/")
                a_path = item.get("answer_path", "").replace("\\", "/")

                # magic-eye/ 접두사가 없으면 추가 (GCS 내 실제 경로 반영)
                if p_path and not p_path.startswith("magic-eye/"):
                    p_path = f"magic-eye/{p_path}"
                if a_path and not a_path.startswith("magic-eye/"):
                    a_path = f"magic-eye/{a_path}"

                p_url = self.gcs_loader.generate_signed_url(p_path, bucket_name=self.bucket_name)
                a_url = self.gcs_loader.generate_signed_url(a_path, bucket_name=self.bucket_name)

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

            return MagicEyeQuizResponse(
                total_count=len(candidates),
                candidates=candidates,
                correct_answer=MagicEyeCorrectAnswer(
                    id=correct_idx,
                    asset_id=correct_item.asset_id
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
