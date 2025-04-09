# Импортируем необходимые модули и библиотеки
# FastAPI для создания API, HTTPException для обработки ошибок
from fastapi import FastAPI, HTTPException
# BaseModel для валидации данных, EmailStr для проверки email
from pydantic import BaseModel, EmailStr
import pymysql  # Для связи с базой данных
from typing import Dict  # Типизация словаря
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum  # Enum для создания перечислений
import random  # Для генерации случайных чисел
import uvicorn  # Для запуска приложения
from db_connection import get_dict_users, save_user, change_db_users

# Создаем экземпляр приложения FastAPI
app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешенные источники
    allow_credentials=True,  # Разрешение на передачу cookies
    # Разрешение всех HTTP-методов (GET, POST, PUT, DELETE и т.д.)
    allow_methods=["*"],
    allow_headers=["*"],  # Разрешение всех заголовков
)


# users: Dict[str, dict] = {}
users = get_dict_users()

# Функция для генерации 6-значного кода верификации


def generate_verification_code() -> str:
    """
    Генерирует случайный 6-значный код.
    Возвращает строку с ведущими нулями, если число меньше 6 цифр.
    """
    code = f"{
        random.randint(
            0,
            999999):06d}"
    return code


# Функция для вывода кода верификации в терминал (для разработки)
def print_verification_code(email: str, code: str):
    """
    Выводит код верификации в терминал в красивом формате.
    Используется только для разработки.
    """
    print("\n" + "═" * 50)  # Разделитель
    # Email пользователя (синий цвет)
    print(f"📧 Получатель: \033[1;34m{email}\033[0m")
    # Код верификации (зеленый цвет)
    print(f"🔢 Код верификации: \033[1;32m{code}\033[0m")
    print("═" * 50 + "\n")  # Разделитель


# Модели запросов для валидации входных данных
class LoginRequest(BaseModel):
    """
    Модель для запроса на вход (логин).
    Поля:
    - email: Email пользователя
    - password: Пароль пользователя
    """
    email: str
    password: str


class RegisterRequest(BaseModel):
    """
    Модель для запроса на регистрацию.
    Поля:
    - email: Email пользователя (валидируется как EmailStr)
    - password: Пароль пользователя
    - nickname: Никнейм пользователя
    """
    email: EmailStr
    password: str
    nickname: str


class VerifyRequest(BaseModel):
    """
    Модель для запроса на верификацию email.
    Поля:
    - email: Email пользователя
    - code: Код верификации
    """
    email: EmailStr
    code: str


class RecoverRequest(BaseModel):
    """
    Модель для запроса на восстановление пароля.
    Поля:
    - email: Email пользователя
    """
    email: EmailStr


class RecoverVerifyRequest(BaseModel):
    """
    Модель для запроса на проверку кода восстановления.
    Поля:
    - email: Email пользователя
    - code: Код восстановления
    """
    email: EmailStr
    code: str


class ChangePasswordRequest(BaseModel):
    """
    Модель для запроса на смену пароля.
    Поля:
    - email: Email пользователя
    - code: Код восстановления
    - password: Новый пароль
    """
    email: EmailStr
    code: str
    password: str


class CodeType(str, Enum):
    """
    Перечисление типов кодов:
    - VERIFICATION: Код для верификации email
    - RECOVERY: Код для восстановления пароля
    """
    VERIFICATION = "verification"
    RECOVERY = "recovery"


class ResendCodeRequest(BaseModel):
    """
    Модель для запроса на повторную отправку кода.
    Поля:
    - email: Email пользователя
    - code_type: Тип кода (verification или recovery)
    """
    email: EmailStr
    code_type: CodeType


# Функция для генерации фиктивного токена
def generate_token(email: str) -> str:
    """
    Генерирует фиктивный токен для пользователя.
    Используется для имитации авторизации.
    """
    return f"fake-token-for-{email}"


# Коды сообщений для локализации ошибок и успешных операций
class ErrorCodes:
    """
    Класс с кодами ошибок и сообщений.
    Используется для стандартизации ответов API.
    """
    ALREADY_VERIFIED = 'already_verified'
    SAVING_FAILED = 'saving_failed'
    NOT_ONE_EMAIL = 'not_one_email'
    USER_NOT_FOUND = "user_not_found"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_EXISTS = "user_exists"
    INVALID_VERIFICATION_CODE = "invalid_verification_code"
    ACCOUNT_NOT_VERIFIED = "account_not_verified"
    PASSWORD_CHANGE_SUCCESS = "password_change_success"
    VERIFICATION_CODE_SENT = "verification_code_sent"
    REGISTRATION_SUCCESS = "registration_success"
    VERIFICATION_SUCCESS = "verification_success"


# Обработчик для входа (логина)
@app.post("/auth/login")
def login(data: LoginRequest):
    """
    Обрабатывает запрос на вход.
    Проверяет email, пароль и статус верификации пользователя.
    """
    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )

    user = users[data.email]  # Получаем данные пользователя

    if user["password"] != data.password:
        # Если пароль неверный, возвращаем ошибку 401
        raise HTTPException(
            status_code=401,
            detail={"code": ErrorCodes.INVALID_CREDENTIALS}
        )

    if not user["verified"]:
        # Если аккаунт не верифицирован, возвращаем ошибку 403
        raise HTTPException(
            status_code=403,
            detail={"code": ErrorCodes.ACCOUNT_NOT_VERIFIED}
        )

    # Возвращаем токен при успешной авторизации
    return {"token": generate_token(data.email)}


# Обработчик для регистрации
@app.post("/auth/register")
def register(data: RegisterRequest):
    """
    Обрабатывает запрос на регистрацию.
    Создает нового пользователя и отправляет код верификации.
    """

    if data.email in users:
        # Если пользователь уже существует, возвращаем ошибку 400
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCodes.USER_EXISTS}
        )

    # Генерируем код верификации
    verification_code = generate_verification_code()

    # Сохраняем данные пользователя в "базу данных"
    trace_back = save_user(
        data.email,
        data.password,
        data.nickname,
        False,
        verification_code)
    if trace_back != 'success':
        raise HTTPException(
            # справить код ошибки
            status_code=500,
            detail={"code": ErrorCodes.SAVING_FAILED}
        )

    # Выводим код верификации в терминал
    print_verification_code(str(data.email), verification_code)

    # Возвращаем сообщение об успешной регистрации
    return {
        "message": {"code": ErrorCodes.REGISTRATION_SUCCESS},
        "verification_code": verification_code  # Только для разработки
    }


# Обработчик для верификации email
@app.post("/auth/verify")
def verify(data: VerifyRequest):
    """
    Обрабатывает запрос на верификацию email.
    Проверяет код верификации и активирует аккаунт.
    """
    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )
    user = users[data.email]

    if data.code != user["verification_code"]:
        # Если код неверный, возвращаем ошибку 400
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCodes.INVALID_VERIFICATION_CODE}
        )
    # Активируем аккаунт
    trace_back = change_db_users(user['email'], (('verified', True)))
    if trace_back != 'success':
        raise HTTPException(
            # справить код ошибки
            status_code=500,
            detail={"code": ErrorCodes.SAVING_FAILED}
        )
    return {
        "token": generate_token(user['email']),
        "message": {"code": ErrorCodes.VERIFICATION_SUCCESS}
    }


# Обработчик для восстановления пароля
@app.post("/auth/recover")
def recover(data: RecoverRequest):
    """
    Обрабатывает запрос на восстановление пароля.
    Отправляет код восстановления на email.
    """

    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )

    user = users[data.email]
    # Генерируем код восстановления
    verification_code = generate_verification_code()
    trace_back = change_db_users(
        user['email'], (('verification_code', verification_code)))
    if trace_back != 'success':
        raise HTTPException(
            # справить код ошибки
            status_code=500,
            detail={"code": ErrorCodes.SAVING_FAILED}
        )

    # Выводим код восстановления в терминал
    print_verification_code(user['email'], verification_code)

    # Возвращаем сообщение об успешной отправке кода
    return {
        "message": {"code": ErrorCodes.VERIFICATION_CODE_SENT},
    }


# Обработчик для проверки кода восстановления
@app.post("/auth/recover/verify")
def recover_verify(data: RecoverVerifyRequest):
    """
    Обрабатывает запрос на проверку кода восстановления.
    """
    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )
    user = users[data.email]
    if data.code != user["verification_code"]:
        # Если код неверный, возвращаем ошибку 400
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCodes.INVALID_VERIFICATION_CODE}
        )
    return {"message": {"code": "recovery_verified"}}


# Обработчик для смены пароля
@app.post("/auth/recover/change")
def change_password(data: ChangePasswordRequest):
    """
    Обрабатывает запрос на смену пароля.
    Проверяет код восстановления и обновляет пароль.
    """
    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )
    user = users[data.email]
    if data.code != user["verification_code"]:
        # Если код неверный, возвращаем ошибку 400
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCodes.INVALID_VERIFICATION_CODE}
        )
    # Обновляем пароль
    trace_back = change_db_users(user['email'],
                                 (('password', data.password)))
    if trace_back != 'success':
        raise HTTPException(
            # справить код ошибки
            status_code=500,
            detail={"code": ErrorCodes.SAVING_FAILED}
        )
    return {
        "token": generate_token(user['email']),
        "message": {"code": ErrorCodes.PASSWORD_CHANGE_SUCCESS}
    }


# Обработчик для повторной отправки кода
@app.post("/auth/verify/resend")
def resend_code(data: ResendCodeRequest):
    """
    Обрабатывает запрос на повторную отправку кода.
    Генерирует новый код и отправляет его на email.
    """
    if data.email not in users:
        # Если пользователь не найден, возвращаем ошибку 404
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCodes.USER_NOT_FOUND}
        )
    user = users[data.email]
    if data.code_type == CodeType.VERIFICATION:
        if user["verified"]:
            # Если аккаунт уже верифицирован, возвращаем ошибку 400
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCodes.ALREADY_VERIFIED}
            )

    # Генерируем новый код
    new_code = generate_verification_code()
    trace_back = change_db_users(
        user['email'], (('verification_code', new_code)))
    if trace_back != 'success':
        raise HTTPException(
            # справить код ошибки
            status_code=500,
            detail={"code": ErrorCodes.SAVING_FAILED}
        )

    # Выводим новый код в терминал
    print_verification_code(user['email'], new_code)

    # Возвращаем сообщение об успешной отправке кода
    return {
        "message": {"code": ErrorCodes.VERIFICATION_CODE_SENT},
    }


# Точка входа в приложение
if __name__ == "__main__":
    # Запускаем приложение на хосте 0.0.0.0 и порту 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
