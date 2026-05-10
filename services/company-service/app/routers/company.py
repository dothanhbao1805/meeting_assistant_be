from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_company_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.services import company_service
from app.core.config import settings

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    name: str = Form(...),
    slug: str = Form(...),
    trello_api_key: str | None = Form(None),
    trello_workspace_id: str | None = Form(None),
    owner_account_id: str = Form(...),
    logo_file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_company_db),
):
    data = CompanyCreate(
        name=name,
        slug=slug,
        trello_api_key=trello_api_key,
        trello_workspace_id=trello_workspace_id,
        owner_account_id=owner_account_id,
    )

    return await company_service.create_company(db, data, logo_file)


@router.get("", response_model=list[CompanyResponse])
async def get_all_companies(db: AsyncSession = Depends(get_company_db)):
    return await company_service.get_all_companies(db)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: str, db: AsyncSession = Depends(get_company_db)
):
    return await company_service.get_company_by_id(db, company_id)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    name: str = Form(...),
    slug: str = Form(...),
    trello_api_key: str | None = Form(None),
    trello_workspace_id: str | None = Form(None),
    owner_account_id: str = Form(...),
    logo_file: UploadFile | None = File(None),
    status: str | None = Form(None),
    db: AsyncSession = Depends(get_company_db),
):
    data = CompanyUpdate(
        name=name,
        slug=slug,
        trello_api_key=trello_api_key,
        trello_workspace_id=trello_workspace_id,
        owner_account_id=owner_account_id,
        status=status,
    )

    return await company_service.update_company(db, company_id, data, logo_file)


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: str, db: AsyncSession = Depends(get_company_db)):
    await company_service.delete_company(db, company_id)


@router.get("/{company_id}/trello/authorize")
async def trello_authorize(
    company_id: str,
    db: AsyncSession = Depends(get_company_db),
):
    """Trả về URL để user bấm vào authorize Trello"""
    company = await company_service.get_company_by_id(db, company_id)

    if not company.trello_api_key:
        raise HTTPException(status_code=400, detail="Chưa có trello_api_key")

    callback_url = f"http://localhost:5173/trello/callback?companyId={company_id}"

    auth_url = (
        f"https://trello.com/1/authorize"
        f"?key={company.trello_api_key}"
        f"&name=MeetingAssistant"
        f"&scope=read,write"
        f"&expiration=never"
        f"&return_url={callback_url}"  # ← đổi response_type=token thành return_url
    )

    return {"auth_url": auth_url}


@router.post("/{company_id}/trello/callback")
async def trello_callback(
    company_id: str,
    token: str,  # Trello gửi ?token=xxx về đây
    db: AsyncSession = Depends(get_company_db),
):
    """Trello redirect về đây sau khi user authorize"""
    await company_service.save_trello_token(db, company_id, token)
    return {"message": "Trello connected successfully", "company_id": company_id}
