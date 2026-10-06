package com.livestockai.app.data.repository

import com.livestockai.app.data.api.ApiClient
import com.livestockai.app.data.local.TokenManager
import com.livestockai.app.domain.model.User
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AuthRepository(private val tokenManager: TokenManager) {

    private val apiService get() = ApiClient.getApiService(tokenManager)

    suspend fun login(email: String, pass: String): Result<User> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.login(mapOf("email" to email, "password" to pass))
            if (response.isSuccessful && response.body()?.status == "success") {
                val body = response.body()!!
                val auth = body.auth
                val userDto = body.user
                if (auth != null && userDto != null) {
                    tokenManager.saveTokens(auth.accessToken, auth.refreshToken)
                    tokenManager.saveUserData(
                        userId = userDto.userId,
                        fullName = userDto.fullName,
                        email = userDto.email,
                        role = userDto.role,
                        phone = userDto.phone
                    )
                    return@withContext Result.success(
                        User(
                            userId = userDto.userId,
                            fullName = userDto.fullName,
                            email = userDto.email,
                            phone = userDto.phone,
                            role = userDto.role,
                            profileImage = userDto.profileImage,
                            sellerId = userDto.sellerId,
                            buyerId = userDto.buyerId
                        )
                    )
                }
            }
            val errorMsg = response.body()?.message ?: "Login failed. Please check your credentials."
            Result.failure(Exception(errorMsg))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun register(
        fullName: String,
        email: String,
        pass: String,
        phone: String,
        role: String,
        adminCode: String = ""
    ): Result<User> = withContext(Dispatchers.IO) {
        try {
            val payload = mutableMapOf(
                "full_name" to fullName,
                "email" to email,
                "password" to pass,
                "phone" to phone,
                "role" to role
            )
            if (adminCode.isNotBlank()) payload["admin_code"] = adminCode

            val response = apiService.register(payload)
            if (response.isSuccessful && response.body()?.status == "success") {
                val body = response.body()!!
                val auth = body.auth
                val userDto = body.user
                if (auth != null && userDto != null) {
                    tokenManager.saveTokens(auth.accessToken, auth.refreshToken)
                    tokenManager.saveUserData(
                        userId = userDto.userId,
                        fullName = userDto.fullName,
                        email = userDto.email,
                        role = userDto.role,
                        phone = userDto.phone
                    )
                    return@withContext Result.success(
                        User(
                            userId = userDto.userId,
                            fullName = userDto.fullName,
                            email = userDto.email,
                            phone = userDto.phone,
                            role = userDto.role
                        )
                    )
                }
            }
            val errorMsg = response.body()?.message ?: "Registration failed. Please try again."
            Result.failure(Exception(errorMsg))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getCurrentUser(): User? {
        val userId = tokenManager.getUserId()
        if (userId == -1) return null
        return User(
            userId = userId,
            fullName = tokenManager.getUserFullName() ?: "",
            email = tokenManager.getUserEmail() ?: "",
            phone = tokenManager.getUserPhone(),
            role = tokenManager.getUserRole()
        )
    }

    fun logout() {
        tokenManager.clear()
    }
}
