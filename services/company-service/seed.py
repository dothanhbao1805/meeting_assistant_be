import asyncio
import uuid
from app.db.database import SessionLocal
from app.models.member import Member, MemberRole
from app.models.company import Company, CompanyStatus

# ── Dữ liệu mẫu ──────────────────────────────────────────
COMPANY_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

COMPANIES = [
    {
        "id": COMPANY_ID,
        "name": "Tech Startup VN",
        "slug": "tech-startup-vn",
        "owner_account_id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "status": CompanyStatus.active,
    }
]

MEMBERS = [
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "company_id": COMPANY_ID,
        "account_id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "full_name": "Nguyen Van A",
        "role": MemberRole.owner,
        "google_email": "nguyenvana@gmail.com",
        "voice_embedding": None,
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "company_id": COMPANY_ID,
        "account_id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "full_name": "Tran Thi B",
        "role": MemberRole.admin,
        "google_email": "tranthib@gmail.com",
        "voice_embedding": None,
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "company_id": COMPANY_ID,
        "account_id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "full_name": "Le Van C",
        "role": MemberRole.member,
        "google_email": "levanc@gmail.com",
        "voice_embedding": None,
    },
]


async def seed():
    async with SessionLocal() as db:
        # ── Tạo company ──────────────────────────────────
        for c in COMPANIES:
            existing = await db.get(Company, c["id"])
            if not existing:
                db.add(Company(**c))
                print(f"✅ Created company: {c['name']}")
            else:
                print(f"⚠️  Company đã tồn tại: {c['name']}")

        await db.commit()

        # ── Tạo members ──────────────────────────────────
        for m in MEMBERS:
            existing = await db.get(Member, m["id"])
            if not existing:
                db.add(Member(**m))
                print(f"✅ Created member: {m['full_name']} ({m['role']})")
            else:
                print(f"⚠️  Member đã tồn tại: {m['full_name']}")

        await db.commit()
        print("\n🎉 Seed xong!")
        print(f"   Company ID : {COMPANY_ID}")
        print(f"   Member IDs :")
        for m in MEMBERS:
            print(f"      {m['full_name']} → {m['id']}")


if __name__ == "__main__":
    asyncio.run(seed())