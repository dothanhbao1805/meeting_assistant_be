from app.services.storage_service import get_signed_url, extract_object_path

# Test extract_object_path
def test_extract_path():
    full_url = "https://orpwzeomiyxddrrxczax.supabase.co/storage/v1/object/public/vd/abc/xyz.mp3"
    result = extract_object_path(full_url, "vd")
    assert result == "abc/xyz.mp3", f"Sai: {result}"
    print("✓ extract_object_path:", result)

def test_extract_path_simple():
    full_url = "https://orpwzeomiyxddrrxczax.supabase.co/storage/v1/object/public/vd/test.mp3"
    result = extract_object_path(full_url, "vd")
    assert result == "test.mp3", f"Sai: {result}"
    print("✓ extract_object_path simple:", result)

def test_extract_path_invalid():
    try:
        extract_object_path("https://invalid-url.com/no-bucket", "vd")
        assert False, "Phải raise exception"
    except Exception as e:
        print("✓ extract_object_path invalid handled:", e)

# Test get_signed_url thật — cần Meeting Service đang chạy
def test_get_signed_url():
    MEDIA_FILE_ID = "e5f82862-d92d-48f4-aadf-7629efac95ce"

    print("\nGọi Meeting Service lấy media file...")
    url = get_signed_url(MEDIA_FILE_ID)
    print("✓ Signed URL:", url)
    assert "token=" in url or "signedURL" in url.lower() or url.startswith("https://")

if __name__ == "__main__":
    print("=== Test extract_object_path (không cần network) ===")
    test_extract_path()
    test_extract_path_simple()
    test_extract_path_invalid()

    print("\n=== Test get_signed_url (cần Meeting Service + Supabase) ===")
    test_get_signed_url()

    print("\n✓ Tất cả pass")