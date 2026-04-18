import re
import cloudinary
import cloudinary.uploader
from app.core.config import settings


class CloudinaryClient:
    _initialized = False

    @classmethod
    def init(cls):
        if cls._initialized:
            return

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )
        cls._initialized = True

    @classmethod
    def upload_image(cls, file, folder: str = "company"):
        cls.init()
        return cloudinary.uploader.upload(file, folder=folder)

    @classmethod
    def delete_by_url(cls, url: str):
        cls.init()
        public_id = cls.extract_public_id(url)
        if not public_id:
            return None
        return cloudinary.uploader.destroy(public_id)

    @staticmethod  # ✅ Đã indent đúng vào trong class
    def extract_public_id(url: str) -> str | None:
        try:
            # Lấy phần sau "/upload/"
            after_upload = url.split("/upload/")[-1]

            # Bỏ version nếu có: v1234567890/...
            after_upload = re.sub(r"^v\d+/", "", after_upload)

            # Bỏ extension: .jpg, .png, ...
            public_id = re.sub(r"\.[^./]+$", "", after_upload)

            return public_id or None
        except Exception:
            return None