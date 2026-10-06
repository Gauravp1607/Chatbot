package com.livestockai.app.ui.screens.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.AuthRepository
import com.livestockai.app.domain.model.User
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Success(val user: User) : AuthState()
    data class Error(val message: String) : AuthState()
}

class AuthViewModel(private val authRepository: AuthRepository) : ViewModel() {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    fun login(email: String, pass: String) {
        if (email.isBlank() || pass.isBlank()) {
            _authState.value = AuthState.Error("Please enter both email and password.")
            return
        }
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            val result = authRepository.login(email.trim(), pass)
            result.onSuccess { user ->
                _authState.value = AuthState.Success(user)
            }.onFailure { error ->
                _authState.value = AuthState.Error(error.message ?: "Login failed")
            }
        }
    }

    fun register(
        fullName: String,
        email: String,
        pass: String,
        phone: String,
        role: String,
        adminCode: String = ""
    ) {
        if (fullName.isBlank() || email.isBlank() || pass.isBlank()) {
            _authState.value = AuthState.Error("Please fill in all required fields.")
            return
        }
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            val result = authRepository.register(
                fullName.trim(),
                email.trim(),
                pass,
                phone.trim(),
                role,
                adminCode
            )
            result.onSuccess { user ->
                _authState.value = AuthState.Success(user)
            }.onFailure { error ->
                _authState.value = AuthState.Error(error.message ?: "Registration failed")
            }
        }
    }

    fun resetState() {
        _authState.value = AuthState.Idle
    }
}
