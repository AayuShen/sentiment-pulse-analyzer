"""Test script: upload audio files and verify pipeline."""
import requests
import time
import json
import os
import glob

BASE = "http://localhost:8000"
DATASET = r"C:\Users\aayus\Downloads\Audio_Dataset\Audio_Dataset"

def upload(file_path, cid, lang=""):
    with open(file_path, "rb") as f:
        r = requests.post(f"{BASE}/api/voice/upload",
            files={"file": (os.path.basename(file_path), f)},
            data={"cid": cid, "lang": lang})
    if r.status_code == 200:
        return r.json().get("job_id")
    print(f"  Upload failed: {r.status_code} {r.text[:200]}")
    return None

def poll(job_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE}/api/voice/status/{job_id}")
            if r.status_code != 200:
                print(f"  [{job_id[:8]}] HTTP {r.status_code}")
                time.sleep(3)
                continue
            d = r.json()
            status = d.get("status", "")
            meta = d.get("meta", {})
            stage = meta.get("stage", status)
            print(f"  [{job_id[:8]}] {stage} - {status}")
            if status in ("SUCCESS", "FAILURE"):
                return d
        except Exception as e:
            print(f"  [{job_id[:8]}] poll error: {e}")
        time.sleep(3)
    return {"status": "TIMEOUT"}

def test_file(folder, cid, lang, filename=None):
    files = sorted(glob.glob(os.path.join(DATASET, folder, "*")))
    files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg'))]
    if filename:
        files = [f for f in files if filename in os.path.basename(f)]
    if not files:
        print(f"  No files found in {folder}")
        return
    fp = files[0]
    name = os.path.basename(fp)
    size_kb = os.path.getsize(fp) / 1024
    print(f"\nUploading: {name} ({size_kb:.0f} KB) as {cid} lang={lang or 'auto'}")
    job_id = upload(fp, cid, lang)
    if not job_id:
        return
    print(f"  Job ID: {job_id}")
    result = poll(job_id, timeout=300)
    if result["status"] == "SUCCESS":
        r = result.get("result", {})
        print(f"  SUCCESS! tag={r.get('tag','?')} id={r.get('id','?')}")
    elif result["status"] == "FAILURE":
        print(f"  FAILED: {result.get('result', '')}")
    else:
        print(f"  {result['status']}")
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Single small English file")
    print("=" * 60)
    test_file("English", "ENG-001", "en", "English_4")
