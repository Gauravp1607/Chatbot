package com.livestockai.app.data.local

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class TokenManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val _isLoggedIn = MutableStateFlow(getAccessToken() != null)
    val isLoggedIn: StateFlow<Boolean> = _isLoggedIn.asStateFlow()

    fun saveTokens(accessToken: String, refreshToken: String) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_REFRESH_TOKEN, refreshToken)
            .apply()
        _isLoggedIn.value = true
    }

    fun getAccessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)

    fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)

    fun saveUserData(userId: Int, fullName: String, email: String, role: String, phone: String? = null) {
        prefs.edit()
            .putInt(KEY_USER_ID, userId)
            .putString(KEY_FULL_NAME, fullName)
            .putString(KEY_EMAIL, email)
            .putString(KEY_ROLE, role)
            .putString(KEY_PHONE, phone)
            .apply()
    }

    fun getUserId(): Int = prefs.getInt(KEY_USER_ID, -1)
    fun getUserFullName(): String? = prefs.getString(KEY_FULL_NAME, null)
    fun getUserEmail(): String? = prefs.getString(KEY_EMAIL, null)
    fun getUserRole(): String = prefs.getString(KEY_ROLE, "Buyer") ?: "Buyer"
    fun getUserPhone(): String? = prefs.getString(KEY_PHONE, null)

    fun clear() {
        prefs.edit().clear().apply()
        _isLoggedIn.value = false
    }

    companion object {
        private const val PREFS_NAME = "livestock_auth_prefs"
        private const val KEY_ACCESS_TOKEN = "jwt_access_token"
        private const val KEY_REFRESH_TOKEN = "jwt_refresh_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_FULL_NAME = "full_name"
        private const val KEY_EMAIL = "email"
        private const val KEY_ROLE = "role"
        private const val KEY_PHONE = "phone"
    }
}
