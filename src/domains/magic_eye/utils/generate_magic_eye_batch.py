import asyncio
import os
from datetime import datetime
from src.domains.magic_eye.consts.magic_eye_assets import MAGIC_EYE_ASSETS
from src.domains.magic_eye.services.magic_eye_service import MagicEyeService
from src.utils.logger import info

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def generate_magic_eye_batch(num_images_per_asset: int = 30):
    output_base_dir = os.path.join(BASE_DIR, "outputs")
    os.makedirs(output_base_dir, exist_ok=True)

    # 서비스 초기화 (GPU 없으면 자동으로 CPU 모드로 로드됨)
    info("🔄 모델 로딩 중... 모델이 메모리에 올라갈 때까지 잠시만 기다려주세요.")
    service = MagicEyeService()

    total_assets = len(MAGIC_EYE_ASSETS)
    total_expected = total_assets * num_images_per_asset
    completed_count = 0

    info(f"🚀 총 {total_assets}개의 사물에 대해 각각 {num_images_per_asset}장씩 생성을 시작합니다.")

    for a_idx, asset in enumerate(MAGIC_EYE_ASSETS, 1):
        asset_id = asset['id']
        asset_display_name = asset['display_name']
        asset_output_dir = os.path.join(output_base_dir, asset_id)
        os.makedirs(asset_output_dir, exist_ok=True)

        info(f"\n📦 [{a_idx}/{total_assets}] 카테고리: {asset_display_name} ({asset_id})")

        for i in range(num_images_per_asset):
            # 파일명 규칙: assetid_순번_prob.png (타임스탬프를 제거하여 고정 파일명으로 체크 가능하게 함)
            # 타임스탬프가 필요하다면 파일 존재 체크 로직을 조금 수정해야 합니다.
            # 여기서는 '순번'을 기준으로 중복을 체크합니다.
            prob_path = os.path.join(asset_output_dir, f"{asset_id}_{i + 1}_prob.png")
            ans_path = os.path.join(asset_output_dir, f"{asset_id}_{i + 1}_ans.png")

            # 1. 이미 파일이 존재하는지 확인 (중간 저장 기능의 핵심)
            if os.path.exists(prob_path) and os.path.exists(ans_path):
                info(f"  [Image {i + 1}/{num_images_per_asset}] 이미 생성됨. 건너뜁니다.")
                completed_count += 1
                continue

            start_time = datetime.now()
            info(f"  [Image {i + 1}/{num_images_per_asset}] 생성 중... (예상 소요 시간: 80초)")

            try:
                # LLM 프롬프트 생성 (실패 시 기본 에셋 프롬프트 사용)
                llm_prompts = await service.prompt_agent.get_diverse_prompts(asset_display_name, count=1)
                base_prompt = llm_prompts[0] if llm_prompts else asset['prompt']

                # 이미지 생성 호출
                generated_image = await service.generate_specific_game(asset, base_prompt)

                # 파일 저장
                with open(prob_path, "wb") as f:
                    f.write(generated_image.problem_image)
                with open(ans_path, "wb") as f:
                    f.write(generated_image.answer_image)

                duration = (datetime.now() - start_time).seconds
                completed_count += 1
                progress = (completed_count / total_expected) * 100
                info(f"    ✅ 완료! ({duration}s) | 전체 진행률: {progress:.1f}%")

            except Exception as e:
                info(f"    ❌ {asset_id} 생성 중 오류 발생: {str(e)}")
                # 오류 발생 시 너무 빨리 반복되지 않도록 잠시 대기
                await asyncio.sleep(2)

    info("\n✨ 모든 배치 생성 작업이 완료되었습니다!")

if __name__ == "__main__":
    # 장당 79초 기준, 900장 생성 시 약 20시간 소요됩니다.
    # 중단되었다가 다시 실행하면 완료된 파일은 건너뛰고 나머지부터 시작합니다.
    asyncio.run(generate_magic_eye_batch(num_images_per_asset=30))