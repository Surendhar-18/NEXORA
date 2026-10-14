import sys
import json
import httpx

API_BASE = "http://127.0.0.1:8000/api/v1"
VALID_MP4_HEADER = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + (b"\x00" * 4096)

def step_upload():
    print("[1] Uploading test video to live API...")
    with httpx.Client() as client:
        files = {"file": ("demo_persistence_clip.mp4", VALID_MP4_HEADER, "video/mp4")}
        data = {"zone_id": "ZONE-01", "sampling_interval_sec": "2.0"}
        res = client.post(f"{API_BASE}/videos/upload", files=files, data=data)
        if res.status_code != 201:
            print(f"[FAIL] Upload returned {res.status_code}: {res.text}")
            sys.exit(1)
        res_data = res.json()
        print(f"    [SUCCESS] Video ID: {res_data['id']}")
        print(f"    [SUCCESS] Status: {res_data['status']}")
        with open("last_test_ids.json", "w") as f:
            json.dump({"video_id": res_data["id"]}, f)

def step_verify():
    print("[2] Verifying persistence after backend restart...")
    with open("last_test_ids.json") as f:
        saved = json.load(f)
    vid_id = saved["video_id"]
    with httpx.Client() as client:
        res = client.get(f"{API_BASE}/videos/{vid_id}")
        if res.status_code != 200:
            print(f"[FAIL] Query returned {res.status_code}: {res.text}")
            sys.exit(1)
        video_data = res.json()
        print(f"    [SUCCESS] Verified video record: {video_data['original_filename']} ({video_data['id']})")
        
        # Check jobs
        jobs_res = client.get(f"{API_BASE}/jobs")
        jobs = jobs_res.json()["jobs"]
        matching_job = next((j for j in jobs if j["video_id"] == vid_id), None)
        if not matching_job:
            print("[FAIL] Associated job not found in database")
            sys.exit(1)
        print(f"    [SUCCESS] Verified job record: {matching_job['id']} (Status: {matching_job['status']})")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        step_verify()
    else:
        step_upload()
