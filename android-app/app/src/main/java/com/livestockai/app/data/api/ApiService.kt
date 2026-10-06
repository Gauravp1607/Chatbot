package com.livestockai.app.data.api

import com.livestockai.app.data.api.dto.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // -------------------------------------------------------------
    // Auth & Profile
    // -------------------------------------------------------------
    @POST("api/v1/auth/register")
    suspend fun register(@Body body: Map<String, String>): Response<AuthResponse>

    @POST("api/v1/auth/login")
    suspend fun login(@Body body: Map<String, String>): Response<AuthResponse>

    @POST("api/v1/auth/refresh")
    suspend fun refreshToken(@Body body: Map<String, String>): Response<AuthResponse>

    @GET("api/v1/auth/profile")
    suspend fun getProfile(): Response<Map<String, Any>>

    // -------------------------------------------------------------
    // Marketplace & Animals
    // -------------------------------------------------------------
    @GET("api/v1/animals")
    suspend fun getAnimals(
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20,
        @Query("q") query: String? = null,
        @Query("type") type: String? = null,
        @Query("breed") breed: String? = null,
        @Query("gender") gender: String? = null,
        @Query("city") city: String? = null,
        @Query("state") state: String? = null,
        @Query("vaccinated") vaccinated: String? = null,
        @Query("min_price") minPrice: Double? = null,
        @Query("max_price") maxPrice: Double? = null,
        @Query("sort_by") sortBy: String = "newest"
    ): Response<AnimalListResponse>

    @GET("api/v1/animals/categories")
    suspend fun getCategories(): Response<CategoryListResponse>

    @GET("api/v1/animals/{id}")
    suspend fun getAnimalDetail(@Path("id") animalId: Int): Response<AnimalDetailResponse>

    @Multipart
    @POST("api/v1/animals")
    suspend fun createAnimal(
        @Part("animal_type") animalType: RequestBody,
        @Part("breed") breed: RequestBody,
        @Part("animal_name") animalName: RequestBody,
        @Part("age") age: RequestBody,
        @Part("weight") weight: RequestBody,
        @Part("gender") gender: RequestBody,
        @Part("price") price: RequestBody,
        @Part("city") city: RequestBody,
        @Part("state") state: RequestBody,
        @Part("milk_yield") milkYield: RequestBody,
        @Part("vaccinated") vaccinated: RequestBody,
        @Part("health_status") healthStatus: RequestBody,
        @Part("description") description: RequestBody,
        @Part image: MultipartBody.Part? = null
    ): Response<Map<String, Any>>

    // -------------------------------------------------------------
    // Wishlist
    // -------------------------------------------------------------
    @GET("api/v1/wishlist")
    suspend fun getWishlist(): Response<WishlistResponse>

    @POST("api/v1/wishlist/toggle/{id}")
    suspend fun toggleWishlist(@Path("id") animalId: Int): Response<WishlistToggleResponse>

    // -------------------------------------------------------------
    // AI Gemini & Disease Scanner
    // -------------------------------------------------------------
    @POST("api/v1/ai/chat")
    suspend fun askAIChat(@Body request: AIChatRequest): Response<AIChatResponse>

    @Multipart
    @POST("api/v1/ai/disease-detect")
    suspend fun scanDisease(
        @Part image: MultipartBody.Part
    ): Response<DiseaseDetectResponse>

    // -------------------------------------------------------------
    // Geolocation Nearby
    // -------------------------------------------------------------
    @GET("api/v1/nearby-animals")
    suspend fun getNearbyAnimals(
        @Query("lat") lat: Double,
        @Query("lng") lng: Double,
        @Query("radius") radiusKm: Double = 50.0
    ): Response<NearbyAnimalsResponse>

    // -------------------------------------------------------------
    // Orders & Checkout
    // -------------------------------------------------------------
    @GET("api/v1/orders")
    suspend fun getOrders(): Response<OrderListResponse>

    @POST("api/v1/orders/create")
    suspend fun createOrder(@Body body: Map<String, Int>): Response<CreateOrderResponse>
}
