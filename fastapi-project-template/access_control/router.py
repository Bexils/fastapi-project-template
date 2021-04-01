from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import dependencies as deps
from access_control import cruds, models, schemas



perms_router = APIRouter(
    prefix='/permissions',
    tags=['Permissions']
)
roles_router = APIRouter(
    prefix='/roles',
    tags=['Roles']
)


# Permissions
@perms_router.post('',
    status_code=201,
    response_model=schemas.PermissionSchema
)
def create_permission(
    perm_data: schemas.PermissionCreate,
    dba: Session = Depends(deps.get_db)
):
    try:
        permission = cruds.create_permission(db=dba, perm_data=perm_data)
    except IntegrityError as e:
        raise HTTPException(
            status_code=403,
            detail='Duplicate permission not allowed'
        )
    else:
        return permission


@perms_router.get('', response_model=List[schemas.PermissionSchema])
def list_permissions(dba: Session = Depends(deps.get_db)):
    return dba.query(models.Permission).all()


@perms_router.get('/{perm_name}',response_model=schemas.PermissionSchema)
def permission_detail(perm_name: str, dba: Session = Depends(deps.get_db)):
    permission = cruds.get_perm_by_name(name=perm_name, db=dba)
    if not permission:
        raise HTTPException(
            status_code=404,
            detail='Permission not found'
        )
    return permission


@perms_router.put('/{perm_name}', response_model=schemas.PermissionSchema)
def update_permission(
    perm_name: str,
    perm_data: schemas.PermissionUpdate,
    dba: Session = Depends(deps.get_db)
):
    permission = cruds.get_perm_by_name(name=perm_name, db=dba)
    if not permission:
        raise HTTPException(
            status_code=404,
            detail='Permission not found'
        )
    perm_update_dict = perm_data.dict(exclude_unset=True)
    if len(perm_update_dict) < 1:
        raise HTTPException(
            status_code=400,
            detail='Invalid request'
        )
    for key, value in perm_update_dict.items():
        setattr(permission, key, value)
    dba.commit()
    dba.refresh(permission)
    return permission


@perms_router.delete('/{perm_name}')
def delete_permission(perm_name: str, dba: Session = Depends(deps.get_db)):
    permission = cruds.get_perm_by_name(db=dba, name=perm_name)
    if not permission:
        raise HTTPException(
            status_code=404,
            detail='Permission not found'
        )
    dba.query(models.Permission). \
        filter(models.Permission.name == perm_name). \
        delete()
    dba.commit()
    return {'detail': 'Permission deleted successfully.'}


#Roles
@roles_router.post('',
    status_code=201,
    response_model=schemas.RoleSchema
)
def create_role(
    role_data: schemas.RoleCreate,
    dba: Session = Depends(deps.get_db)
):
    try:
        role = cruds.create_role(db=dba, role_data=role_data)
    except IntegrityError as e:
        raise HTTPException(
            status_code=403,
            detail='Duplicate role not allowed'
        )
    else:
        return role


@roles_router.get('', response_model=List[schemas.RoleSchema])
def list_roles(dba: Session = Depends(deps.get_db)):
    return dba.query(models.Role).all()


@roles_router.get('/{role_name}',response_model=schemas.RoleSchema)
def role_detail(role_name: str, dba: Session = Depends(deps.get_db)):
    role = cruds.get_role_by_name(name=role_name, db=dba)
    if not role:
        raise HTTPException(
            status_code=404,
            detail='Role not found'
        )
    return role


@roles_router.put(
    '/{role_name}',
    response_model=schemas.RoleSchema
)
def update_role(
    role_name: str,
    role_data: schemas.RoleUpdate,
    dba: Session = Depends(deps.get_db)
):
    role = cruds.get_role_by_name(name=role_name, db=dba)
    if not role:
        raise HTTPException(
            status_code=404,
            detail='Role not found'
        )
    role_dict = role_data.dict(exclude_unset=True)
    try:
        perms = role_dict.pop('permissions')
    except KeyError:
        pass
    else:
        for perm_name in perms:
            perm = cruds.get_perm_by_name(name=perm_name, db=dba)
            if perm:
                role.permissions.append(perm)

    for key, value in role_dict.items():
        setattr(role, key, value)
    dba.commit()
    dba.refresh(role)
    return role


@roles_router.delete('/{role_name}')
def delete_role(role_name: str, dba: Session = Depends(deps.get_db)):
    role = cruds.get_role_by_name(db=dba, name=role_name)
    if not role:
        raise HTTPException(
            status_code=404,
            detail='Role not found'
        )
    dba.query(models.Role). \
        filter(models.Role.name == role_name). \
        delete()
    dba.commit()
    return {'detail': 'Role deleted successfully.'}
