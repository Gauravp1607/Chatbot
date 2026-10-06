package com.livestockai.app.data.api.dto

import com.google.gson.annotations.SerializedName

data class AuthTokensDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    @SerializedName("token_type") val tokenType: String = "Bearer",
    @SerializedName("expires_in") val expiresIn: Long = 0
)

data class UserDto(
    @SerializedName("user_id") val userId: Int,
    @SerializedName("full_name") val fullName: String,
    @SerializedName("email") val email: String,
    @SerializedName("phone") val phone: String? = null,
    @SerializedName("role") val role: String = "Buyer",
    @SerializedName("profile_image") val profileImage: String? = null,
    @SerializedName("address") val address: String? = null,
    @SerializedName("city") val city: String? = null,
    @SerializedName("state") val state: String? = null,
    @SerializedName("seller_id") val sellerId: Int? = null,
    @SerializedName("buyer_id") val buyerId: Int? = null
)

data class AuthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("message") val message: String? = null,
    @SerializedName("user") val user: UserDto? = null,
    @SerializedName("auth") val auth: AuthTokensDto? = null
)

data class AnimalDto(
    @SerializedName("animal_id") val animalId: Int,
    @SerializedName("seller_id") val sellerId: Int,
    @SerializedName("animal_type") val animalType: String,
    @SerializedName("breed") val breed: String,
    @SerializedName("animal_name") val animalName: String? = null,
    @SerializedName("age") val age: Int = 0,
    @SerializedName("weight") val weight: Double = 0.0,
    @SerializedName("gender") val gender: String = "Male",
    @SerializedName("price") val price: Double = 0.0,
    @SerializedName("city") val city: String? = null,
    @SerializedName("state") val state: String? = null,
    @SerializedName("latitude") val latitude: Double? = null,
    @SerializedName("longitude") val longitude: Double? = null,
    @SerializedName("milk_yield") val milkYield: Double = 0.0,
    @SerializedName("vaccinated") val vaccinated: String = "No",
    @SerializedName("health_status") val healthStatus: String = "Healthy",
    @SerializedName("availability") val availability: String = "Available",
    @SerializedName("image_url") val imageUrl: String? = null,
    @SerializedName("primary_image") val primaryImage: String? = null,
    @SerializedName("description") val description: String? = null,
    @SerializedName("seller_name") val sellerName: String? = null,
    @SerializedName("seller_rating") val sellerRating: Double? = null,
    @SerializedName("seller_verified") val sellerVerified: Any? = null,
    @SerializedName("distance_km") val distanceKm: Double? = null
)

data class AnimalListResponse(
    @SerializedName("status") val status: String,
    @SerializedName("page") val page: Int = 1,
    @SerializedName("limit") val limit: Int = 20,
    @SerializedName("total") val total: Int = 0,
    @SerializedName("total_pages") val totalPages: Int = 1,
    @SerializedName("animals") val animals: List<AnimalDto> = emptyList()
)

data class AnimalDetailResponse(
    @SerializedName("status") val status: String,
    @SerializedName("animal") val animal: AnimalDto? = null,
    @SerializedName("vaccinations") val vaccinations: List<Map<String, Any>> = emptyList(),
    @SerializedName("disease_history") val diseaseHistory: List<Map<String, Any>> = emptyList()
)

data class CategoryListResponse(
    @SerializedName("status") val status: String,
    @SerializedName("animal_types") val animalTypes: List<String> = emptyList(),
    @SerializedName("breeds") val breeds: List<Map<String, String>> = emptyList()
)

data class AIChatRequest(
    @SerializedName("message") val message: String
)

data class AIChatResponse(
    @SerializedName("status") val status: String,
    @SerializedName("reply") val reply: String? = null,
    @SerializedName("message") val message: String? = null,
    @SerializedName("response") val response: String? = null,
    @SerializedName("timestamp") val timestamp: String? = null
)

data class DiagnosisDto(
    @SerializedName("disease_name") val diseaseName: String,
    @SerializedName("confidence") val confidence: Double = 0.0,
    @SerializedName("severity") val severity: String = "Medium",
    @SerializedName("animal_type") val animalType: String = "Livestock",
    @SerializedName("symptoms") val symptoms: List<String> = emptyList(),
    @SerializedName("immediate_care") val immediateCare: String = "",
    @SerializedName("home_remedies") val homeRemedies: String = "",
    @SerializedName("veterinary_action") val veterinaryAction: String = ""
)

data class DiseaseDetectResponse(
    @SerializedName("status") val status: String,
    @SerializedName("image_url") val imageUrl: String? = null,
    @SerializedName("diagnosis") val diagnosis: DiagnosisDto? = null,
    @SerializedName("message") val message: String? = null
)

data class NearbyAnimalsResponse(
    @SerializedName("status") val status: String,
    @SerializedName("count") val count: Int = 0,
    @SerializedName("radius_km") val radiusKm: Double = 50.0,
    @SerializedName("animals") val animals: List<AnimalDto> = emptyList()
)

data class WishlistResponse(
    @SerializedName("status") val status: String,
    @SerializedName("wishlist") val wishlist: List<AnimalDto> = emptyList()
)

data class WishlistToggleResponse(
    @SerializedName("status") val status: String,
    @SerializedName("action") val action: String,
    @SerializedName("message") val message: String
)

data class OrderDto(
    @SerializedName("order_id") val orderId: Int,
    @SerializedName("animal_id") val animalId: Int,
    @SerializedName("animal_name") val animalName: String? = null,
    @SerializedName("animal_type") val animalType: String? = null,
    @SerializedName("breed") val breed: String? = null,
    @SerializedName("price") val price: Double = 0.0,
    @SerializedName("buyer_payable_amount") val buyerPayableAmount: Double? = null,
    @SerializedName("order_status") val orderStatus: String = "Pending",
    @SerializedName("payment_status") val paymentStatus: String = "Pending",
    @SerializedName("image_url") val imageUrl: String? = null,
    @SerializedName("seller_name") val sellerName: String? = null,
    @SerializedName("buyer_name") val buyerName: String? = null,
    @SerializedName("created_at") val createdAt: String? = null
)

data class OrderListResponse(
    @SerializedName("status") val status: String,
    @SerializedName("orders") val orders: List<OrderDto> = emptyList()
)

data class CreateOrderResponse(
    @SerializedName("status") val status: String,
    @SerializedName("order_id") val orderId: Int,
    @SerializedName("amount_payable") val amountPayable: String,
    @SerializedName("currency") val currency: String = "INR",
    @SerializedName("message") val message: String
)
