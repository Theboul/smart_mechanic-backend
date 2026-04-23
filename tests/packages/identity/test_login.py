import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.packages.identity.application.auth_use_cases.login_user import LoginUserUseCase
from app.packages.identity.domain.models import Usuario
from app.packages.identity.presentation.schemas.auth_schemas import UserLogin
from app.core.exceptions import UnauthorizedError

@pytest.mark.asyncio
async def test_login_success():
    # Setup
    mock_repo = MagicMock()
    email = "test@example.com"
    password = "password123"
    
    # Simular usuario encontrado
    mock_user = MagicMock(spec=Usuario)
    mock_user.id_usuario = uuid.uuid4()
    mock_user.correo = email
    mock_user.contrasena = "hashed_password" 
    mock_user.estado = True
    mock_user.rol_nombre = "cliente"
    mock_user.nombre = "Juan Perez"
    mock_user.telefono = "12345678"
    
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)
    
    # Mock de las funciones de seguridad
    with patch("app.packages.identity.application.auth_use_cases.login_user.verify_password", return_value=True), \
         patch("app.packages.identity.application.auth_use_cases.login_user.create_access_token", return_value="fake_jwt_token"):
        
        use_case = LoginUserUseCase(mock_repo)
        user_in = UserLogin(correo=email, contrasena=password)
        result = await use_case.execute(user_in)

        # Assertions
        assert result.access_token == "fake_jwt_token"
        assert result.user.correo == email
        mock_repo.get_by_email.assert_called_once_with(email)

@pytest.mark.asyncio
async def test_login_invalid_password():
    # Setup
    mock_repo = MagicMock()
    mock_user = MagicMock(spec=Usuario)
    mock_user.contrasena = "hashed_password"
    mock_repo.get_by_email = AsyncMock(return_value=mock_user)

    # Simular que la contraseña NO coincide
    with patch("app.packages.identity.application.auth_use_cases.login_user.verify_password", return_value=False):
        use_case = LoginUserUseCase(mock_repo)
        user_in = UserLogin(correo="test@example.com", contrasena="wrong")
        
        with pytest.raises(UnauthorizedError):
            await use_case.execute(user_in)
