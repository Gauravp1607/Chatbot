package com.livestockai.app.ui.screens.ai

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.livestockai.app.data.repository.AIRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
    val timestamp: Long = System.currentTimeMillis()
)

data class AIChatUiState(
    val messages: List<ChatMessage> = listOf(
        ChatMessage(
            text = "Hello! I am your **Livestock AI Assistant**. Ask me anything about cattle nutrition, vaccination schedules, cow/dog/horse/cat symptoms, or livestock marketplace prices!",
            isUser = false
        )
    ),
    val isLoading: Boolean = false,
    val currentInput: String = ""
)

class AIChatViewModel(private val aiRepository: AIRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(AIChatUiState())
    val uiState: StateFlow<AIChatUiState> = _uiState.asStateFlow()

    fun onInputChanged(input: String) {
        _uiState.value = _uiState.value.copy(currentInput = input)
    }

    fun sendMessage(text: String? = null) {
        val prompt = (text ?: _uiState.value.currentInput).trim()
        if (prompt.isBlank() || _uiState.value.isLoading) return

        val userMessage = ChatMessage(text = prompt, isUser = true)
        _uiState.value = _uiState.value.copy(
            messages = _uiState.value.messages + userMessage,
            currentInput = "",
            isLoading = true
        )

        viewModelScope.launch {
            val result = aiRepository.sendMessage(prompt)
            val replyText = result.getOrElse { error ->
                "I apologize, I could not process your query right now. Please check your internet connection or ask about cows, dogs, cats, or horses."
            }

            val assistantMessage = ChatMessage(text = replyText, isUser = false)
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + assistantMessage,
                isLoading = false
            )
        }
    }
}
