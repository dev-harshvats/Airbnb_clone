from fastapi import APIRouter

from app.core.container import CurrentUser, NoStore, UserServiceDep
from app.schemas.user import HostProfileOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"], dependencies=[NoStore])


# `/me` routes are declared before `/{user_id}` so "me" is never parsed as an id.
@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: CurrentUser, service: UserServiceDep):
    return service.update_profile(user, body.model_dump(exclude_unset=True))


@router.post("/me/become-host", response_model=UserOut)
def become_host(user: CurrentUser, service: UserServiceDep):
    return service.become_host(user)


@router.get("/{user_id}", response_model=HostProfileOut)
def host_profile(user_id: int, service: UserServiceDep):
    return service.get_host_profile(user_id)
