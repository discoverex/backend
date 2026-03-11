import csv
import io
import json
import sys
from pathlib import Path

from src.configs.setting import BASE_DIR, BUCKET_NAME

# 프로젝트 루트(BASE_DIR)를 sys.path에 추가하여 상위 모듈 임포트 가능하게 함
current_file = Path(__file__).resolve()

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# ruff: noqa: E402
from src.configs import setting
from src.utils.gcs_image_loader import get_gcs_image_loader
from src.utils.logger import logger
def fetch_and_save_magic_eye_metadata():
    """
    GCS에서 매직아이 메타데이터(CSV)를 가져와 "split": "test"인 정보만 JSON으로 저장합니다.
    """
    bucket_name = "discoverex-image-storage"
    blob_name = "magic-eye/metadata.csv"

    # 저장될 폴더 및 파일 경로 (BASE_DIR/metadata/)
    metadata_dir = setting.BASE_DIR / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    json_file_path = metadata_dir / "magic_eye_metadata.json"

    print(f"[*] GCS {bucket_name} 버킷에서 {blob_name} 파일을 가져오는 중입니다...")

    try:
        gcs_loader = get_gcs_image_loader()
        csv_bytes = gcs_loader.download_image_as_bytes(blob_name, bucket_name=bucket_name)

        if csv_bytes is None:
            print(f"[!] 에러: GCS에서 파일을 찾을 수 없습니다: {blob_name}")
            return

        csv_text = csv_bytes.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # "split": "test" 필터링 및 숫자 변환
        test_metadata = []
        for row in csv_reader:
            if row.get("split") == "test":
                # file_number 등 숫자로 취급해야 할 필드 변환
                for key in ["file_number", "file_no"]:
                    if key in row and row[key]:
                        try:
                            row[key] = int(row[key])
                        except (ValueError, TypeError):
                            pass
                test_metadata.append(row)

        print(f"[*] 필터링 완료: {len(test_metadata)} 건 (split='test')")

        # JSON으로 저장
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(test_metadata, f, ensure_ascii=False, indent=4)

        print(f"[+] 저장 성공! 경로: {json_file_path}")
        print(f"[*] 총 {len(test_metadata)}개의 데이터가 로컬에 캐싱되었습니다.")

    except Exception as e:
        print(f"[!] 예기치 못한 에러가 발생했습니다: {str(e)}")
        logger.error(f"메타데이터 fetch/save 실패: {str(e)}")


if __name__ == "__main__":
    fetch_and_save_magic_eye_metadata()
