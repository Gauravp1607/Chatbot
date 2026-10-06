package com.livestockai.app.data.api

import com.livestockai.app.data.local.TokenManager
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    // Server IP address and port
    private var baseUrl = "http://192.168.1.18:5000/"

    fun setCustomBaseUrl(url: String) {
        baseUrl = if (url.endsWith("/")) url else "$url/"
        retrofitInstance = null
    }

    fun getBaseUrl(): String = baseUrl

    fun getImageUrl(filename: String?): String {
        if (filename.isNullOrBlank()) return ""
        if (filename.startsWith("http://") || filename.startsWith("https://")) return filename
        
        val cleanName = filename.trim().removePrefix("/")
        
        // If filename already contains static/ or uploads/, handle it
        if (cleanName.startsWith("static/")) {
            return "$baseUrl$cleanName"
        }
        if (cleanName.startsWith("uploads/")) {
            return "${baseUrl}static/$cleanName"
        }
        
        return "${baseUrl}static/uploads/$cleanName"
    }

    private var retrofitInstance: Retrofit? = null
    private var okHttpClient: OkHttpClient? = null

    fun getOkHttpClient(tokenManager: TokenManager): OkHttpClient {
        if (okHttpClient == null) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val authInterceptor = Interceptor { chain ->
                val requestBuilder = chain.request().newBuilder()
                val token = tokenManager.getAccessToken()
                if (!token.isNullOrBlank()) {
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
                requestBuilder.addHeader("Accept", "application/json")
                chain.proceed(requestBuilder.build())
            }

            okHttpClient = OkHttpClient.Builder()
                .addInterceptor(authInterceptor)
                .addInterceptor(loggingInterceptor)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(60, TimeUnit.SECONDS)
                .build()
        }
        return okHttpClient!!
    }

    fun getApiService(tokenManager: TokenManager): ApiService {
        if (retrofitInstance == null) {
            val client = getOkHttpClient(tokenManager)

            retrofitInstance = Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }

        return retrofitInstance!!.create(ApiService::class.java)
    }
}
