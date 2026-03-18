from src.configs.minio import get_minio_client
from src.utils.logger import error

def get_job_folders() -> list[str]:
    """
    orchestrator-artifacts 버킷의 jobs/ 경로에 있는 폴더 목록을 조회합니다.
    """
    bucket_name = "orchestrator-artifacts"
    prefix = "jobs/"
    
    try:
        client = get_minio_client()
        # recursive=False를 사용하여 하위 폴더(Prefix)만 가져옵니다.
        objects = client.list_objects(bucket_name, prefix=prefix, recursive=False)
        
        folders = []
        for obj in objects:
            if obj.is_dir:
                folder_name = obj.object_name.replace(prefix, "").strip("/")
                if folder_name:
                    folders.append(folder_name)
        
        return folders
    except Exception as e:
        error(f"MinIO 작업 폴더 목록 조회 실패: {str(e)}")
        # 예외를 그대로 던져서 서비스/라우터에서 처리하게 함
        raise e
