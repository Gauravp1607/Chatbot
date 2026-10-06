package com.livestockai.app.domain.model

data class Animal(
    val animalId: Int,
    val sellerId: Int,
    val animalType: String,
    val breed: String,
    val animalName: String,
    val age: Int = 0,
    val weight: Double = 0.0,
    val gender: String = "Male",
    val price: Double = 0.0,
    val city: String? = null,
    val state: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val milkYield: Double = 0.0,
    val vaccinated: String = "No",
    val healthStatus: String = "Healthy",
    val availability: String = "Available",
    val imageUrl: String? = null,
    val description: String? = null,
    val sellerName: String? = null,
    val sellerRating: Double? = null,
    val sellerVerified: Boolean = false,
    val distanceKm: Double? = null,
    val isFavorite: Boolean = false
) {
    val isVaccinated: Boolean get() = vaccinated.equals("Yes", ignoreCase = true) || vaccinated == "1"
    
    val formattedPrice: String get() = "₹%,.0f".format(price)
    
    val displayLocation: String get() = when {
        !city.isNullOrBlank() && !state.isNullOrBlank() -> "$city, $state"
        !city.isNullOrBlank() -> city
        !state.isNullOrBlank() -> state
        else -> "India"
    }

    val formattedDistance: String get() = distanceKm?.let {
        if (it < 1.0) "<1 km away" else "%.1f km away".format(it)
    } ?: ""
}
