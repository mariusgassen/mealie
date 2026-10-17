import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm.session import Session

from mealie.core.config import get_app_settings
from mealie.core.settings.static import APP_VERSION
from mealie.db.db_setup import generate_session
from mealie.db.models.users.users import User
from mealie.repos.all_repositories import get_repositories
from mealie.schema.admin.about import AppInfo, AppStartupInfo, AppTheme
from mealie.services.app_theme import AppThemeService
from mealie.services.app_theme.app_icons import ICO_NAME, icon_etag, icon_ico, icon_png

router = APIRouter(prefix="/about")


@router.get("", response_model=AppInfo)
def get_app_info(session: Session = Depends(generate_session)):
    """Get general application information"""
    settings = get_app_settings()

    public_repos = get_repositories(session, group_id=None, household_id=None)

    default_group_slug: str | None = None
    default_household_slug: str | None = None

    default_group = public_repos.groups.get_by_name(settings.DEFAULT_GROUP)
    if default_group and default_group.preferences and not default_group.preferences.private_group:
        default_group_slug = default_group.slug

    if default_group and default_group_slug:
        group_repos = get_repositories(session, group_id=default_group.id, household_id=None)
        default_household = group_repos.households.get_by_name(settings.DEFAULT_HOUSEHOLD)
        if default_household and default_household.preferences and not default_household.preferences.private_household:
            default_household_slug = default_household.slug

    return AppInfo(
        version=APP_VERSION,
        demo_status=settings.IS_DEMO,
        production=settings.PRODUCTION,
        allow_signup=settings.ALLOW_SIGNUP,
        default_group_slug=default_group_slug,
        default_household_slug=default_household_slug,
        enable_oidc=settings.OIDC_READY,
        oidc_redirect=settings.OIDC_AUTO_REDIRECT,
        oidc_provider_name=settings.OIDC_PROVIDER_NAME,
        enable_reverse_proxy_auth=settings.REVERSE_PROXY_AUTH_READY,
        allow_password_login=settings.ALLOW_PASSWORD_LOGIN,
        token_time=settings.TOKEN_TIME,
        allowed_iframe_hosts=settings.allowed_iframe_hosts,
        branding_name=settings.branding.name,
        branding_logo_url="/api/app/about/branding-logo" if settings.branding.logo_file else None,
    )


@router.get("/startup-info", response_model=AppStartupInfo)
def get_startup_info(session: Session = Depends(generate_session)):
    """returns helpful startup information"""
    settings = get_app_settings()

    is_first_login = False
    with session as db:
        if db.query(User).filter_by(email=settings._DEFAULT_EMAIL).count() > 0:
            is_first_login = True

    return AppStartupInfo(
        is_first_login=is_first_login,
        is_demo=settings.IS_DEMO,
    )


@router.get("/theme", response_model=AppTheme)
def get_app_theme(resp: Response, session: Session = Depends(generate_session)):
    """Get's the current theme settings"""
    repos = get_repositories(session, group_id=None, household_id=None)

    # admins can change the theme at any time, so clients must always revalidate instead of caching it for days
    resp.headers["Cache-Control"] = "no-cache"
    return AppThemeService(repos).effective()


@router.get("/icons/{name}", response_class=Response, include_in_schema=True)
def get_app_icon(name: str, request: Request, session: Session = Depends(generate_session)):
    """The app icon / favicon, drawn in the server's primary color so it follows the theme"""
    repos = get_repositories(session, group_id=None, household_id=None)
    primary = AppThemeService(repos).effective().light_primary

    etag = icon_etag(name, primary)
    headers = {"Cache-Control": "no-cache", "ETag": etag}

    if name != ICO_NAME and icon_png(name, primary) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    if name == ICO_NAME:
        return Response(content=icon_ico(primary), media_type="image/x-icon", headers=headers)

    return Response(content=icon_png(name, primary), media_type="image/png", headers=headers)


@router.get("/branding-logo", response_class=FileResponse)
def get_app_branding_logo():
    """Get's the custom branding logo, if configured"""
    settings = get_app_settings()

    logo_file = settings.branding.logo_file
    if logo_file is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    media_type = mimetypes.guess_type(logo_file)[0]
    return FileResponse(logo_file, media_type=media_type, headers={"Cache-Control": "public, max-age=604800"})
