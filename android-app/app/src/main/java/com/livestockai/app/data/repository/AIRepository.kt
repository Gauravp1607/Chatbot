package com.livestockai.app.data.repository

import com.livestockai.app.data.api.ApiClient
import com.livestockai.app.data.api.dto.AIChatRequest
import com.livestockai.app.data.local.TokenManager
import com.livestockai.app.domain.model.DiagnosisResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

class AIRepository(private val tokenManager: TokenManager) {

    private val apiService get() = ApiClient.getApiService(tokenManager)

    suspend fun sendMessage(prompt: String): Result<String> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.askAIChat(AIChatRequest(prompt))
            if (response.isSuccessful && response.body()?.status == "success") {
                val reply = response.body()?.reply ?: response.body()?.response ?: "I am processing your query."
                return@withContext Result.success(reply)
            }
            val errorMsg = response.body()?.message ?: "AI Assistant is temporarily unavailable."
            Result.failure(Exception(errorMsg))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun detectDisease(imageFile: File): Result<DiagnosisResult> = withContext(Dispatchers.IO) {
        try {
            val reqFile = imageFile.asRequestBody("image/*".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("image", imageFile.name, reqFile)

            val response = apiService.scanDisease(body)
            if (response.isSuccessful && response.body()?.status == "success") {
                val diag = response.body()?.diagnosis
                val imageUrl = ApiClient.getImageUrl(response.body()?.imageUrl)
                if (diag != null) {
                    return@withContext Result.success(
                        DiagnosisResult(
                            diseaseName = diag.diseaseName,
                            confidence = diag.confidence,
                            severity = diag.severity,
                            animalType = diag.animalType,
                            symptoms = diag.symptoms,
                            immediateCare = diag.immediateCare,
                            homeRemedies = diag.homeRemedies,
                            veterinaryAction = diag.veterinaryAction,
                            imageUrl = imageUrl
                        )
                    )
                }
            }
            Result.failure(Exception(response.body()?.message ?: "Diagnosis analysis failed."))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
