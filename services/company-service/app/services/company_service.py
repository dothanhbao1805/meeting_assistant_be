from fastapi import HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cloudinary import CloudinaryClient
from app.models.company import Company
from app.repositories import company_repo
from app.schemas.company import CompanyCreate, CompanyUpdate

async def get_company_by_id(db: AsyncSession, company_id: str) -> Company:
    company = await company_repo.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company

async def get_all_companies(db: AsyncSession) -> list[Company]:
    companies = await company_repo.get_all_companies(db)
    if not companies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Companies not found",
        )
    return companies

async def create_company(db: AsyncSession, data: CompanyCreate, logo_file: UploadFile | None = None):
    existing = await company_repo.get_company_by_slug(db, data.slug)

    if existing:
        raise HTTPException(status_code=400, detail="Slug has been used")

    logo_url = None

    if logo_file:
        upload_result = CloudinaryClient.upload_image(
            logo_file.file,
            folder="company"
        )

        logo_url = upload_result.get("secure_url")

    company_data = data.model_dump()
    company_data["logo_url"] = logo_url

    return await company_repo.create_company(db, company_data)


async def update_company(
    db: AsyncSession,
    company_id: str,
    data: CompanyUpdate,
    logo_file: UploadFile | None = None
):
    company = await company_repo.get_company_by_id(db, company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)

    if logo_file:
        if company.logo_url:
            CloudinaryClient.delete_by_url(company.logo_url)

        upload_result = CloudinaryClient.upload_image(
            logo_file.file,
            folder="company"
        )

        update_data["logo_url"] = upload_result.get("secure_url")

    return await company_repo.update_company(db, company_id, update_data)

async def delete_company(db: AsyncSession, company_id: str) -> None:
    company = await company_repo.get_company_by_id(db, company_id)
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if company.logo_url:
        CloudinaryClient.delete_by_url(company.logo_url)

    await company_repo.delete_company(db, company_id)