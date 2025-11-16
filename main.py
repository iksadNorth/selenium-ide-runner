import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from src.parser import extract_failed_tests

app = FastAPI(title="Selenium IDE Runner API", version="1.0.0")

# 경로 설정
SCENARIOS_DIR = Path("scenarios")
REPORTS_DIR = Path("reports")
SELENIUM_GRID_URL = os.getenv("SELENIUM_GRID_URL", "http://localhost:4444/wd/hub")

# 디렉토리 생성
SCENARIOS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# selenium-side-runner 경로 확인
SELENIUM_SIDE_RUNNER = shutil.which("selenium-side-runner")
if not SELENIUM_SIDE_RUNNER:
    raise RuntimeError("selenium-side-runner를 찾을 수 없습니다. 설치되어 있는지 확인하세요.")


class SideFileInfo(BaseModel):
    side_id: str
    filename: str
    size: int


class ExecutionResult(BaseModel):
    side_id: str
    status: str
    report_path: Optional[str] = None
    message: Optional[str] = None


def get_side_file_path(side_id: str) -> Path:
    """side_id에 해당하는 파일 경로 반환"""
    # side_id가 .side 확장자를 포함하지 않으면 추가
    if not side_id.endswith(".side"):
        side_id = f"{side_id}.side"
    return SCENARIOS_DIR / side_id


def is_valid_side_file(file_path: Path) -> bool:
    """유효한 .side 파일인지 확인"""
    if not file_path.exists() or not file_path.suffix == ".side":
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Selenium IDE 파일 형식 검증
            return "version" in data and "tests" in data
    except (json.JSONDecodeError, KeyError):
        return False


@app.get("/sides", response_model=List[SideFileInfo])
async def list_sides():
    """사이드 파일 목록 조회"""
    side_files = []
    
    if not SCENARIOS_DIR.exists():
        return []
    
    for file_path in SCENARIOS_DIR.glob("*.side"):
        if is_valid_side_file(file_path):
            side_files.append({
                "side_id": file_path.stem,  # 확장자 제외
                "filename": file_path.name,
                "size": file_path.stat().st_size
            })
    
    return side_files


@app.get("/sides/{side_id}")
async def download_side(side_id: str):
    """사이드 파일 다운로드"""
    file_path = get_side_file_path(side_id)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"사이드 파일을 찾을 수 없습니다: {side_id}")
    
    if not is_valid_side_file(file_path):
        raise HTTPException(status_code=400, detail=f"유효하지 않은 사이드 파일입니다: {side_id}")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/json"
    )


@app.post("/sides/{side_id}", response_model=ExecutionResult)
async def execute_side(side_id: str):
    """사이드 파일 재현 (Selenium Grid로 실행)"""
    file_path = get_side_file_path(side_id)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"사이드 파일을 찾을 수 없습니다: {side_id}")
    
    if not is_valid_side_file(file_path):
        raise HTTPException(status_code=400, detail=f"유효하지 않은 사이드 파일입니다: {side_id}")
    
    try:
        # selenium-side-runner 실행
        cmd = [
            SELENIUM_SIDE_RUNNER,
            "--server", SELENIUM_GRID_URL,
            str(file_path),
            "--output-directory", str(REPORTS_DIR)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        # 최신 리포트 파일 찾기
        report_files = sorted(
            REPORTS_DIR.glob("results-*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        report_path = str(report_files[0]) if report_files else None
        
        if result.returncode == 0:
            return ExecutionResult(
                side_id=side_id,
                status="success",
                report_path=report_path,
                message="테스트가 성공적으로 실행되었습니다."
            )
        else:
            return ExecutionResult(
                side_id=side_id,
                status="failed",
                report_path=report_path,
                message=f"테스트 실행 중 오류가 발생했습니다: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="테스트 실행 시간이 초과되었습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"테스트 실행 중 오류가 발생했습니다: {str(e)}")


@app.patch("/sides/{side_id}")
async def upload_side(side_id: str, file: UploadFile = File(...)):
    """사이드 파일 업로드"""
    # 파일 확장자 검증
    if not file.filename.endswith(".side"):
        raise HTTPException(status_code=400, detail="파일 확장자는 .side여야 합니다.")
    
    file_path = get_side_file_path(side_id)
    
    try:
        # 파일 내용 읽기
        content = await file.read()
        
        # JSON 유효성 검증
        try:
            data = json.loads(content.decode("utf-8"))
            if "version" not in data or "tests" not in data:
                raise HTTPException(status_code=400, detail="유효하지 않은 Selenium IDE 파일 형식입니다.")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="유효하지 않은 JSON 파일입니다.")
        
        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "side_id": side_id,
            "filename": file_path.name,
            "size": len(content),
            "message": "파일이 성공적으로 업로드되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")


@app.delete("/sides/{side_id}")
async def delete_side(side_id: str):
    """사이드 파일 삭제"""
    file_path = get_side_file_path(side_id)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"사이드 파일을 찾을 수 없습니다: {side_id}")
    
    try:
        file_path.unlink()
        return {
            "side_id": side_id,
            "message": "파일이 성공적으로 삭제되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "selenium_grid_url": SELENIUM_GRID_URL}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

