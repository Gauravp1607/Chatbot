package com.livestockai.app.data.repository

import com.livestockai.app.data.api.ApiClient
import com.livestockai.app.data.api.dto.AnimalDto
import com.livestockai.app.data.local.TokenManager
import com.livestockai.app.domain.model.Animal
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class MarketplaceRepository(private val tokenManager: TokenManager) {

    private val apiService get() = ApiClient.getApiService(tokenManager)

    suspend fun getAnimals(
        page: Int = 1,
        query: String? = null,
        type: String? = null,
        breed: String? = null,
        gender: String? = null,
        vaccinated: String? = null,
        minPrice: Double? = null,
        maxPrice: Double? = null,
        sortBy: String = "newest"
    ): Result<List<Animal>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getAnimals(
                page = page,
                query = query,
                type = type,
                breed = breed,
                gender = gender,
                vaccinated = vaccinated,
                minPrice = minPrice,
                maxPrice = maxPrice,
                sortBy = sortBy
            )
            if (response.isSuccessful && response.body()?.status == "success") {
                val dtos = response.body()?.animals ?: emptyList()
                return@withContext Result.success(dtos.map { it.toDomain() })
            }
            Result.failure(Exception("Failed to fetch animals: ${response.message()}"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getAnimalDetail(animalId: Int): Result<Animal> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getAnimalDetail(animalId)
            if (response.isSuccessful && response.body()?.status == "success") {
                val dto = response.body()?.animal
                if (dto != null) {
                    return@withContext Result.success(dto.toDomain())
                }
            }
            Result.failure(Exception("Animal not found"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getCategories(): Result<List<String>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getCategories()
            if (response.isSuccessful && response.body()?.status == "success") {
                return@withContext Result.success(response.body()?.animalTypes ?: emptyList())
            }
            Result.failure(Exception("Failed to load categories"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getWishlist(): Result<List<Animal>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getWishlist()
            if (response.isSuccessful && response.body()?.status == "success") {
                val items = response.body()?.wishlist ?: emptyList()
                return@withContext Result.success(items.map { it.toDomain().copy(isFavorite = true) })
            }
            Result.failure(Exception("Failed to fetch wishlist"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun toggleWishlist(animalId: Int): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.toggleWishlist(animalId)
            if (response.isSuccessful && response.body()?.status == "success") {
                val action = response.body()?.action
                return@withContext Result.success(action == "added")
            }
            Result.failure(Exception("Wishlist update failed"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getNearbyAnimals(lat: Double, lng: Double, radius: Double = 50.0): Result<List<Animal>> =
        withContext(Dispatchers.IO) {
            try {
                val response = apiService.getNearbyAnimals(lat, lng, radius)
                if (response.isSuccessful && response.body()?.status == "success") {
                    val dtos = response.body()?.animals ?: emptyList()
                    return@withContext Result.success(dtos.map { it.toDomain() })
                }
                Result.failure(Exception("Failed to load nearby animals"))
            } catch (e: Exception) {
                Result.failure(e)
            }
        }

    suspend fun createAnimalListing(
        animalType: String,
        breed: String,
        animalName: String,
        age: Int,
        weight: Double,
        gender: String,
        price: Double,
        city: String,
        state: String,
        milkYield: Double,
        vaccinated: Boolean,
        healthStatus: String,
        description: String,
        imageFile: File? = null
    ): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val textPlain = "text/plain".toMediaTypeOrNull()

            val typePart = animalType.toRequestBody(textPlain)
            val breedPart = breed.toRequestBody(textPlain)
            val namePart = animalName.toRequestBody(textPlain)
            val agePart = age.toString().toRequestBody(textPlain)
            val weightPart = weight.toString().toRequestBody(textPlain)
            val genderPart = gender.toRequestBody(textPlain)
            val pricePart = price.toString().toRequestBody(textPlain)
            val cityPart = city.toRequestBody(textPlain)
            val statePart = state.toRequestBody(textPlain)
            val milkPart = milkYield.toString().toRequestBody(textPlain)
            val vaccPart = (if (vaccinated) "1" else "0").toRequestBody(textPlain)
            val healthPart = healthStatus.toRequestBody(textPlain)
            val descPart = description.toRequestBody(textPlain)

            var imagePart: MultipartBody.Part? = null
            if (imageFile != null && imageFile.exists()) {
                val reqFile = imageFile.asRequestBody("image/*".toMediaTypeOrNull())
                imagePart = MultipartBody.Part.createFormData("image", imageFile.name, reqFile)
            }

            val response = apiService.createAnimal(
                typePart, breedPart, namePart, agePart, weightPart, genderPart, pricePart,
                cityPart, statePart, milkPart, vaccPart, healthPart, descPart, imagePart
            )

            if (response.isSuccessful) {
                return@withContext Result.success(true)
            }
            Result.failure(Exception("Failed to create animal listing: ${response.message()}"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun AnimalDto.toDomain(): Animal {
        val rawImage = imageUrl ?: primaryImage
        val resolvedImage = ApiClient.getImageUrl(rawImage)
        val isVerified = when (sellerVerified) {
            is Boolean -> sellerVerified
            is Number -> sellerVerified.toInt() == 1
            is String -> sellerVerified == "1" || sellerVerified.equals("true", true)
            else -> false
        }

        return Animal(
            animalId = animalId,
            sellerId = sellerId,
            animalType = animalType,
            breed = breed,
            animalName = animalName ?: "$animalType $breed",
            age = age,
            weight = weight,
            gender = gender,
            price = price,
            city = city,
            state = state,
            latitude = latitude,
            longitude = longitude,
            milkYield = milkYield,
            vaccinated = vaccinated,
            healthStatus = healthStatus,
            availability = availability,
            imageUrl = resolvedImage,
            description = description,
            sellerName = sellerName,
            sellerRating = sellerRating,
            sellerVerified = isVerified,
            distanceKm = distanceKm
        )
    }
}
