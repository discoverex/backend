import base64
import glob
import io
import os

from PIL import Image
from fastapi import APIRouter, HTTPException, Response

from src.common.dtos.wrapped_response import WrappedResponse
from src.configs.setting import APP_ENV
from src.domains.magic_eye.dtos.magic_eye_game_response import MagicEyeGameResponse
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService

magic_eye_router = APIRouter(prefix="/magic-eye", tags=["매직아이"])

# 서비스 인스턴스 (의존성 주입 생략하고 단순화)
magic_eye_service = MagicEyeService()


@magic_eye_router.post("/start", response_model=WrappedResponse[MagicEyeGameResponse])
async def start_game():
    """랜덤하게 매직아이 문제를 생성하고 정답 정보를 반환합니다."""
    try:
        result = await magic_eye_service.generate_random_game()

        # Base64 인코딩 (JSON 반환용)
        prob_b64 = base64.b64encode(result.problem_image).decode('utf-8')
        ans_b64 = base64.b64encode(result.answer_image).decode('utf-8')

        return {
            "data": {
                "problem": f"data:image/png;base64,{prob_b64}",
                "answer": f"data:image/png;base64,{ans_b64}",
                "answer_key": result.target_info.display_name,  # 화면 표시용
                "acceptable_words": result.target_info.keywords  # 정답 판정용
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@magic_eye_router.get(
    "/debug/last-game",
    include_in_schema=(APP_ENV == "local") # 로컬 개발 환경일 때만 스웨거에 표시
)
async def debug_preview():
    """
    개발 전용: 로컬 debug_outputs 폴더에서 가장 최근에 생성된
    문제와 정답 이미지를 찾아 합쳐서 보여줍니다. (추가 생성 없음)
    운영 환경(production)에서는 403 에러를 반환합니다.
    """
    # 운영 서버 실행 차단 (이중 보안)
    if APP_ENV != "local":
        raise HTTPException(
            status_code=403,
            detail="이 엔드포인트는 로컬 개발 환경에서만 사용할 수 있습니다."
        )

    debug_path = "debug_outputs"

    # 1. 디렉토리 존재 확인
    if not os.path.exists(debug_path):
        raise HTTPException(status_code=404, detail="생성된 디버그 이미지가 없습니다. 먼저 /start를 호출하세요.")

    # 2. 가장 최근에 생성된 problem 이미지 찾기
    problem_files = glob.glob(f"{debug_path}/*_problem.png")
    if not problem_files:
        raise HTTPException(status_code=404, detail="저장된 문제 이미지가 없습니다.")

    # 수정 시간 기준 정렬하여 가장 최근 파일 선택
    latest_problem = max(problem_files, key=os.path.getmtime)
    # 파일명 패턴이 {timestamp}_{id}_problem.png 이므로 대응하는 answer 파일 경로 유추
    latest_answer = latest_problem.replace("_problem.png", "_answer.png")

    if not os.path.exists(latest_answer):
        raise HTTPException(status_code=404, detail="대응하는 정답 이미지를 찾을 수 없습니다.")

    try:
        # 3. 파일 읽기 (새로 생성하지 않음!)
        prob_img = Image.open(latest_problem)
        ans_img = Image.open(latest_answer)

        # 4. 이미지 합치기
        combined = Image.new("RGB", (prob_img.width + ans_img.width + 10, prob_img.height), (255, 0, 0))
        combined.paste(prob_img, (0, 0))
        combined.paste(ans_img, (prob_img.width + 10, 0))

        # 5. 반환
        out = io.BytesIO()
        combined.save(out, format="PNG")

        print(f"🔎 Previewing latest files: {os.path.basename(latest_problem)}")
        return Response(content=out.getvalue(), media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 로드 실패: {str(e)}")